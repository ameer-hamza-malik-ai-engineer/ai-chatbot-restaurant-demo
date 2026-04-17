import os
import re
import json
from pathlib import Path
from huggingface_hub import InferenceClient
from dotenv import load_dotenv

load_dotenv()  # loads .env locally; no-op on Streamlit Cloud

# --- Configuration ---
MODEL = "openai/gpt-oss-120b"
MENU_FILE = Path(__file__).parent / "menu.txt"


class Query:
    def __init__(self, query):
        self.new_query = query

    def get_query(self):
        return self.new_query
    
    def set_query(self, query):
        self.new_query = query

new_query = Query("")


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

- When you CONFIRM an order has been placed, you MUST explicitly say:
  "Your order has been placed."
- When you CONFIRM a reservation has been confirmed, you MUST explicitly say:
  "Your reservation has been confirmed."
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


def query_with_history(query, chat_history):
    client = get_client()

    prompt = f"""
        Given the chat history, rewrite the new question to be standalone and searchable. Just rewrite the question:\n\n{chat_history}\n\nQuestion: {query}"
    """

    completion = client.chat.completions.create(
        model=MODEL,
        messages=[
            {
                "role": "user",
                "content": prompt
            }
        ],
        max_tokens=512,
        temperature=0.3,
    )
    return completion.choices[0].message.content



def ask_bot(user_input: str, chat_history: list[dict]) -> str:
    """Send a message to the LLM and return the assistant reply.

    Args:
        user_input: The latest message from the user.
        chat_history: List of prior {"role": ..., "content": ...} messages.

    Returns:
        The assistant's response text.
    """
    # global new_query
    # new_query.set_query(user_input)

    if not user_input or not user_input.strip():
        return "It looks like you didn't type anything. How can I help you today?"

    # if chat_history is not None:
    #     new_query.set_query(query_with_history(user_input, chat_history))

    # Build messages array
    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    messages.extend(chat_history)
    messages.append({"role": "user", "content": user_input})
    # print("New query: ", new_query.get_query())
    # messages.append({"role": "user", "content": new_query.get_query()})

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


# _EXTRACTION_PROMPT = """\
# You are a data extractor. Analyse the conversation below.

# Has the LAST assistant message just CONFIRMED a completed order OR a completed reservation?

# - A confirmation means the assistant explicitly told the customer their order or reservation is confirmed/placed/booked, not merely collected info.

# If the last assistant message confirms an ORDER reply with ONLY this JSON (no markdown, no extra text):
# {"type": "order", "customer_name": "...", "items": ["item1 x2", "item2 x1"], "total": "$X.XX"}

# If the last assistant message confirms a RESERVATION reply with ONLY this JSON (no markdown, no extra text):
# {"type": "reservation", "customer_name": "...", "date": "YYYY-MM-DD or descriptive date", "time": "HH:MM or descriptive time", "guests": N}

# If neither case applies, reply with ONLY the word: null
# """

_EXTRACTION_PROMPT = """\
    You are a strict JSON extractor.

Look ONLY at the LAST assistant message in the conversation.

A confirmation is ONLY valid if the assistant clearly says one of:
- "Your order has been placed"
- "Your reservation has been confirmed"

If it's an ORDER, extract:
{"type": "order", "customer_name": "...", "items": ["..."], "total": "$X.XX"}

If it's a RESERVATION, extract:
{"type": "reservation", "customer_name": "...", "date": "...", "time": "...", "guests": N}

If the last assistant message does NOT contain one of those exact confirmation phrases, return:
null

Return ONLY valid JSON or null. No explanation.

The JSON must be complete, properly closed, and parseable.
Do not stop mid-generation.
"""


def extract_confirmed_action(chat_history: list[dict]) -> dict | None:
    """Detect whether the last assistant turn confirmed an order or reservation.

    Args:
        chat_history: Full conversation including the latest assistant reply.

    Returns:
        Parsed dict with 'type' key ('order' or 'reservation') and relevant fields,
        or None if no confirmation was detected.
    """
    messages = [{"role": "system", "content": _EXTRACTION_PROMPT}]
    messages.extend(chat_history)

    try:
        client = get_client()
        response = client.chat.completions.create(
            model=MODEL,
            messages=messages,
            max_tokens=300,
            temperature=0,
        )
        raw = (response.choices[0].message.content or "").strip()
        print("Raw extraction result: ", raw)
        if not raw or raw.lower() == "null":
            return None
        # Strip accidental markdown code fences
        raw = re.sub(r"^```[a-z]*\n?|```$", "", raw, flags=re.MULTILINE).strip()
        data = json.loads(raw)
        print("Data: ", data)
        if isinstance(data, dict) and data.get("type") in ("order", "reservation"):
            return data
    except Exception:
        pass
    return None
        
