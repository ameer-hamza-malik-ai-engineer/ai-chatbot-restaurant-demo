import streamlit as st
from chatbot import ask_bot, extract_confirmed_action
from database import init_db, save_order, save_reservation, get_orders, get_reservations

# Ensure DB tables exist (runs once per process)
init_db()

# --- Page configuration ---
st.set_page_config(
    page_title="Foodies Hub AI Assistant",
    page_icon="🍔",
    layout="centered",
)

# --- Custom CSS for a polished look ---
st.markdown("""
<style>
    /* Overall page */
    .block-container {
        max-width: 720px;
        padding-top: 2rem;
    }

    /* Header area */
    .header-container {
        text-align: center;
        padding: 1.5rem 0 0.5rem 0;
    }
    .header-container h1 {
        margin-bottom: 0.2rem;
    }
    .header-subtitle {
        color: #888;
        font-size: 1.05rem;
        margin-bottom: 0.5rem;
    }
    .header-divider {
        border: none;
        border-top: 2px solid #ff4b4b;
        width: 60px;
        margin: 0.8rem auto 1.2rem auto;
    }

    /* Header action buttons (scoped to main content area) */
    .main div[data-testid="column"] .stButton > button {
        border-radius: 999px !important;
        font-size: 0.82rem !important;
        padding: 0.3rem 0.6rem !important;
        border: 1px solid #3a3a4a !important;
        background: #262730 !important;
        color: #fafafa !important;
        width: 100%;
        transition: background 0.2s, border-color 0.2s;
    }
    .main div[data-testid="column"] .stButton > button:hover {
        background: #ff4b4b !important;
        border-color: #ff4b4b !important;
        color: #fff !important;
    }

    /* Chat message tweaks */
    .stChatMessage {
        border-radius: 12px !important;
    }
</style>
""", unsafe_allow_html=True)

# --- Header ---
st.markdown("""
<div class="header-container">
    <h1>🤖 AI Restaurant Assistant</h1>
    <p class="header-subtitle">24/7 automated customer support for <strong>Foodies Hub</strong></p>
    <hr class="header-divider">
</div>
""", unsafe_allow_html=True)

# --- Header quick-action buttons ---
_hcol1, _hcol2, _hcol3, _hcol4 = st.columns(4)
with _hcol1:
    if st.button("📋 Menu & Prices", use_container_width=True):
        st.session_state.pending_input = "Show me the entire menu items"
        st.rerun()
with _hcol2:
    if st.button("🛒 Order Food", use_container_width=True):
        st.session_state.pending_input = "I'd like to place a food order."
        st.rerun()
with _hcol3:
    if st.button("📅 Reservations", use_container_width=True):
        st.session_state.pending_input = "Make a reservation for me."
        st.rerun()
with _hcol4:
    if st.button("⏰ Hours & Location", use_container_width=True):
        st.session_state.pending_input = "What are your opening hours and location?"
        st.rerun()

# --- Session state init ---
if "messages" not in st.session_state:
    # Welcome message from assistant
    welcome = (
        "Hey there! 👋 Welcome to **Foodies Hub**! "
        "I'm Foodie, your virtual assistant. I can help you with our menu, "
        "take your order, or book a table. What can I do for you today?"
    )
    st.session_state.messages = [{"role": "assistant", "content": welcome}]
if "pending_input" not in st.session_state:
    st.session_state.pending_input = None
if "processed_confirmations" not in st.session_state:
    st.session_state.processed_confirmations = []

# --- Render chat history ---
for msg in st.session_state.messages:
    avatar = "🍔" if msg["role"] == "assistant" else "👤"
    with st.chat_message(msg["role"], avatar=avatar):
        st.markdown(msg["content"])

# --- Resolve pending input from quick-action buttons ---
typed_input = st.chat_input("Type your message here...")
user_input = typed_input or st.session_state.pop("pending_input", None)

if user_input:
    # Show user message
    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.chat_message("user", avatar="👤"):
        st.markdown(user_input)

    # Build history for bot (all messages except the one just appended)
    history = [
        {"role": m["role"], "content": m["content"]}
        for m in st.session_state.messages[:-1]
    ]

    # Get bot response
    with st.chat_message("assistant", avatar="🍔"):
        with st.spinner(""):
            reply = ask_bot(user_input, history)
        st.markdown(reply)

    st.session_state.messages.append({"role": "assistant", "content": reply})

    # --- Detect and persist confirmed orders / reservations ---
    last_idx = len(st.session_state.messages) - 1
    if last_idx not in st.session_state.processed_confirmations:
        action = extract_confirmed_action(st.session_state.messages)
        if action:
            try:
                if action.get("type") == "order":
                    oid = save_order(
                        action.get("customer_name", "Guest"),
                        action.get("items", []),
                        action.get("total", ""),
                    )
                    st.toast(f"✅ Order #{oid} saved to database!", icon="🛒")
                elif action.get("type") == "reservation":
                    rid = save_reservation(
                        action.get("customer_name", "Guest"),
                        action.get("date", ""),
                        action.get("time", ""),
                        action.get("guests", 1),
                    )
                    st.toast(f"✅ Reservation #{rid} saved to database!", icon="📅")
            except Exception as db_err:
                st.toast(f"⚠️ Could not save to database: {db_err}", icon="⚠️")
        st.session_state.processed_confirmations.append(last_idx)

# --- Sidebar ---
with st.sidebar:
    st.markdown("### 🍔 Foodies Hub")
    st.markdown("---")
    st.markdown(
        "**Hours:** 10 AM – 11 PM\n\n"
        "**Location:** 123 Main Street\n\n"
        "**Phone:** (555) 123-4567"
    )
    st.markdown("---")
    st.markdown("#### Quick Actions")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("📋 See Menu", use_container_width=True):
            st.session_state.pending_input = "Show me the entire menu items"
            st.rerun()
    with col2:
        if st.button("📅 Reserve", use_container_width=True):
            st.session_state.pending_input = "Make a reservation for me."
            st.rerun()

    st.markdown("---")
    if st.button("🗑️ Clear Chat", use_container_width=True):
        st.session_state.messages = []
        st.rerun()

    # --- Recent Orders ---
    st.markdown("---")
    with st.expander("🛒 Recent Orders", expanded=False):
        orders = get_orders(limit=10)
        if orders:
            for o in orders:
                items_str = ", ".join(o["items"]) if isinstance(o["items"], list) else o["items"]
                st.markdown(
                    f"**#{o['id']} — {o['customer_name']}**  \n"
                    f"{items_str}  \n"
                    f"Total: {o['total'] or 'N/A'} · {o['placed_at'][:16].replace('T', ' ')}"
                )
                st.divider()
        else:
            st.caption("No orders yet.")

    # --- Recent Reservations ---
    with st.expander("📅 Recent Reservations", expanded=False):
        reservations = get_reservations(limit=10)
        if reservations:
            for r in reservations:
                st.markdown(
                    f"**#{r['id']} — {r['customer_name']}**  \n"
                    f"{r['date']} at {r['time']} · {r['guests']} guest(s)  \n"
                    f"Booked: {r['placed_at'][:16].replace('T', ' ')}"
                )
                st.divider()
        else:
            st.caption("No reservations yet.")

    st.markdown(
        "<div style='text-align:center; color:#666; font-size:0.75rem; margin-top:2rem;'>"
        "Powered by AI · Demo by Foodies Hub"
        "</div>",
        unsafe_allow_html=True,
    )
