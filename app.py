import streamlit as st
from chatbot import ask_bot

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

    /* Badge pills */
    .badge-row {
        display: flex;
        justify-content: center;
        gap: 0.6rem;
        flex-wrap: wrap;
        margin-bottom: 1.5rem;
    }
    .badge {
        background: #262730;
        color: #fafafa;
        padding: 0.3rem 0.85rem;
        border-radius: 999px;
        font-size: 0.82rem;
        border: 1px solid #3a3a4a;
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
<div class="badge-row">
    <span class="badge">📋 Menu & Prices</span>
    <span class="badge">🛒 Order Food</span>
    <span class="badge">📅 Reservations</span>
    <span class="badge">⏰ Hours & Location</span>
</div>
""", unsafe_allow_html=True)

# --- Session state init ---
if "messages" not in st.session_state:
    st.session_state.messages = []
    # Welcome message from assistant
    welcome = (
        "Hey there! 👋 Welcome to **Foodies Hub**! "
        "I'm Foodie, your virtual assistant. I can help you with our menu, "
        "take your order, or book a table. What can I do for you today?"
    )
    st.session_state.messages.append({"role": "assistant", "content": welcome})

# --- Render chat history ---
for msg in st.session_state.messages:
    avatar = "🍔" if msg["role"] == "assistant" else "👤"
    with st.chat_message(msg["role"], avatar=avatar):
        st.markdown(msg["content"])

# --- Chat input ---
if user_input := st.chat_input("Type your message here..."):
    # Show user message
    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.chat_message("user", avatar="👤"):
        st.markdown(user_input)

    # Build history for bot (exclude the welcome message for cleaner context)
    history = [
        {"role": m["role"], "content": m["content"]}
        for m in st.session_state.messages[:-1]  # exclude current user msg
    ]

    # Get bot response
    with st.chat_message("assistant", avatar="🍔"):
        with st.spinner(""):
            reply = ask_bot(user_input, history)
        st.markdown(reply)

    st.session_state.messages.append({"role": "assistant", "content": reply})

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
            st.session_state.messages.append({"role": "user", "content": "Show me the full menu"})
            st.rerun()
    with col2:
        if st.button("📅 Reserve", use_container_width=True):
            st.session_state.messages.append({"role": "user", "content": "I'd like to make a reservation"})
            st.rerun()

    st.markdown("---")
    if st.button("🗑️ Clear Chat", use_container_width=True):
        st.session_state.messages = []
        st.rerun()

    st.markdown(
        "<div style='text-align:center; color:#666; font-size:0.75rem; margin-top:2rem;'>"
        "Powered by AI · Demo by Foodies Hub"
        "</div>",
        unsafe_allow_html=True,
    )
