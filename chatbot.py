import os
from pathlib import Path
from huggingface_hub import InferenceClient
from dotenv import load_dotenv

load_dotenv()  # loads .env locally; no-op on Streamlit Cloud

# --- Configuration ---
MODEL = "openai/gpt-oss-120b"
MENU_FILE = Path(__file__).parent / "menu.txt"


def _get_api_key() -> str:
    """Load HF API key from .env (local) or st.secrets (Streamlit Cloud)."""
    key = os.getenv("HF_API_KEY", "")
    if not key:
        try:
            import streamlit as st  # only available in Streamlit context
            key = st.secrets.get("HF_API_KEY", "")
        except Exception:
            pass
    return key

# --- Load knowledge base ---
def load_context() -> str:
    try:
        return MENU_FILE.read_text(encoding="utf-8")
    except FileNotFoundError:
        return "Menu information is currently unavailable."

RESTAURANT_CONTEXT = load_context()

# --- System prompt ---
SYSTEM_PROMPT = f"""You are a friendly, professional assistant for Foodies Hub restaurant. Your name is Foodie.

RESTAURANT INFORMATION:
{RESTAURANT_CONTEXT}

BEHAVIOR RULES:
- Greet customers warmly and be conversational, like a real person working at the restaurant.
- Answer menu questions accurately using the information above.
- When a customer wants to ORDER: ask for the item(s), quantity, and their name for the order. Confirm the order and total before finishing.
- When a customer wants a RESERVATION: ask for their name, preferred date, time, and number of guests. Confirm all details before finishing.
- Guide the customer step-by-step; don't ask for everything at once.
- Keep responses concise — 1-3 sentences unless more detail is needed.
- Use a warm, natural tone. Vary your language so you don't sound repetitive.
- If you don't know something, say so honestly and offer to help with something else.
- Never mention that you're reading from a file, context, or document.
- Never break character. You ARE the restaurant assistant.
- Use currency formatting ($X.XX) when discussing prices.
- If a customer seems undecided, make a friendly suggestion from the menu.
"""


def get_client() -> InferenceClient:
    """Create and return an InferenceClient pointed at HuggingFace."""
    api_key = _get_api_key()
    # print(api_key)
    if not api_key:
        raise ValueError(
            "HF_API_KEY is not set. Add it to your .env file or Streamlit secrets."
        )
    return InferenceClient(
        provider="fireworks-ai",
        api_key=api_key,
    )


def ask_bot(user_input: str, chat_history: list[dict]) -> str:
    """Send a message to the LLM and return the assistant reply.

    Args:
        user_input: The latest message from the user.
        chat_history: List of prior {"role": ..., "content": ...} messages.

    Returns:
        The assistant's response text.
    """
    if not user_input or not user_input.strip():
        return "It looks like you didn't type anything. How can I help you today?"

    # Build messages array
    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    messages.extend(chat_history)
    messages.append({"role": "user", "content": user_input})

    try:
        client = get_client()
        response = client.chat.completions.create(
            model=MODEL,
            messages=messages,
            max_tokens=512,
            temperature=0.7,
        )
        reply = response.choices[0].message.content
        return reply.strip() if reply else "Sorry, I didn't catch that. Could you rephrase?"
    except ValueError as exc:
        return f"⚠️ Configuration error: {exc}"
    except Exception as exc:
        return f"⚠️ API error ({type(exc).__name__}): {exc}"
        
