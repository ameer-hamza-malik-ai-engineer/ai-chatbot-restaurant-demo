# 🤖 AI Restaurant Assistant — Foodies Hub

A production-ready AI chatbot demo for a restaurant business, built with **Streamlit** and **Hugging Face Inference API**.

The chatbot can answer menu questions, take food orders, handle table reservations, and respond like a professional restaurant assistant.

![Python](https://img.shields.io/badge/Python-3.10+-blue)
![Streamlit](https://img.shields.io/badge/Streamlit-1.32+-red)

---

## Features

- 📋 **Menu Q&A** — browse items, prices, and specials
- 🛒 **Order Taking** — guided step-by-step ordering flow
- 📅 **Reservations** — conversational booking with structured info collection
- 💬 **Natural Conversation** — warm, human-like responses
- 🕐 **24/7 Availability** — always-on customer support demo

---

## Project Structure

```
ai-chatbot-demo/
├── app.py              # Streamlit frontend
├── chatbot.py          # LLM logic (Hugging Face)
├── menu.txt            # Restaurant knowledge base
├── requirements.txt    # Python dependencies
├── .env                # API key (not committed)
└── README.md
```

---

## Setup

### 1. Clone the repository

```bash
git clone https://github.com/your-username/ai-chatbot-demo.git
cd ai-chatbot-demo
```

### 2. Create a virtual environment (recommended)

```bash
python -m venv .venv
.venv\Scripts\activate        # Windows
# source .venv/bin/activate   # macOS / Linux
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Add your API key

Open the `.env` file and replace the placeholder with your Hugging Face API token:

```
HF_API_KEY=hf_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

> Get a free token at [huggingface.co/settings/tokens](https://huggingface.co/settings/tokens).
> Make sure the token has **Inference API** access.

### 5. Run the app

```bash
streamlit run app.py
```

The app will open in your browser at `http://localhost:8501`.

---

## Configuration

| Setting         | Location               | Default               |
| --------------- | ---------------------- | --------------------- |
| API Key         | `.env` → `HF_API_KEY`  | —                     |
| LLM Model       | `chatbot.py` → `MODEL` | `openai/gpt-oss-120b` |
| Restaurant data | `menu.txt`             | Foodies Hub           |

To customize for a different restaurant, simply edit `menu.txt` with the new business info.

---

## How It Works

1. **Knowledge base** (`menu.txt`) is loaded into memory at startup.
2. A **system prompt** instructs the LLM to act as the restaurant's assistant, grounded in the knowledge base.
3. The **Streamlit frontend** manages chat history in `session_state` and sends the full conversation to the LLM on each turn.
4. The LLM (via Hugging Face's OpenAI-compatible API) generates a contextual reply.

---

## License

MIT — free to use for demos and client presentations.
