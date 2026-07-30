# Virtual AI Clinician — Symptom Triage Console

An LLM-powered, safety-first symptom triage assistant. Built with a FastAPI
backend (retrieval-grounded reasoning + rule-based safety layer, powered by
Groq's free, OpenAI-compatible API) and a custom HTML/CSS/JS chat console — no build
tools required.

## Architecture

```
User message
   │
   ▼
Safety layer (safety.py)  ──► if red-flag phrase found, short-circuit
   │                              and return an emergency instruction
   │ (no red flags)
   ▼
Retrieval layer (retrieval.py) ──► TF-IDF search over data/conditions.csv
   │                                 returns top matching conditions
   ▼
LLM reasoning (Groq API + prompts.py)
   │   grounded in retrieved context, returns structured JSON:
   │   { follow_up_question | possible_conditions, triage_level,
   │     advice, medicine_category, reasoning, disclaimer }
   ▼
Frontend renders either a follow-up question or a triage card
```

## Project structure

```
virtual-ai-clinician/
├── backend/
│   ├── main.py          FastAPI app (serves API + frontend)
│   ├── safety.py         Red-flag / emergency detection
│   ├── retrieval.py       TF-IDF retrieval over the dataset
│   ├── prompts.py        LLM system prompt
│   ├── requirements.txt
│   └── .env.example      Copy to .env and add your API key
├── data/
│   └── conditions.csv    Curated symptom/condition knowledge base
├── frontend/
│   ├── index.html
│   ├── style.css
│   └── script.js
└── README.md
```

## Setup

### 1. Get a FREE Groq API key

1. Go to **https://console.groq.com/keys**
2. Sign in with email, Google, or GitHub
3. Click **"Create API Key"** — no credit card required
4. Copy the key immediately (starts with `gsk_...`) — Groq only shows it once

This is a genuinely free, ongoing tier (not a one-time trial), with generous
daily rate limits — more than enough for building and demoing this project.

> ⚠️ **Treat your API key like a password.** Never paste it into chat
> messages, screenshots, commit it to GitHub, or share it publicly. If a
> key is ever exposed, delete it in AI Studio and generate a new one.

### 2. Create a virtual environment and install dependencies

```bash
cd virtual-ai-clinician/backend
python -m venv venv

# Activate it:
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

pip install -r requirements.txt
```

### 3. Add your API key

```bash
# still inside backend/
cp .env.example .env       # macOS/Linux
copy .env.example .env      # Windows
```

Open `.env` in VS Code and paste your key:
```
GROQ_API_KEY=gsk_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

### 4. Run the app (single command — serves both API and UI)

```bash
uvicorn main:app --reload
```

Then open your browser at:
```
http://localhost:8000
```

That's it — one server serves the chat UI and the API together, so there's
nothing else to start.

## Test it

Try these in the chat box to see all three triage paths:

| Input | Expected result |
|---|---|
| "I have a runny nose and sore throat since yesterday" | 🟢 Self-care |
| "I've had a headache and mild fever for 4 days" | 🟡 Consult a doctor |
| "I have chest pain and shortness of breath" | 🔴 Emergency (safety layer triggers instantly, bypasses the LLM) |

## Customizing the knowledge base

Add or edit rows in `data/conditions.csv`. Each row needs: `condition`,
`symptoms`, `triage_level`, `advice`, `medicine_category`, `see_doctor_if`.
No re-training needed — the retrieval index rebuilds automatically each
time the server starts.

## Notes for your report / viva

- **Why TF-IDF instead of embeddings?** It's lightweight, deterministic,
  and requires no model download — reliable to demo on any machine.
- **Why rule-based safety layer instead of trusting the LLM?** Emergency
  detection must never depend on a probabilistic model. The red-flag
  check in `safety.py` runs before the LLM is even called.
- **Why Groq instead of a paid API?** Groq offers a genuinely free,
  ongoing tier (rate-limited, not a trial) with an OpenAI-compatible
  interface, making the project fully reproducible at zero cost — a fair
  engineering tradeoff to disclose honestly if asked.
- **Why medicine *categories* and not drug names/doses?** This mirrors how
  real triage tools operate — recommending exact medication is a
  prescribing decision, not a triage decision.
- **Limitations to disclose honestly:** curated dataset covers ~34
  conditions (not 900+), no clinical validation, prototype only.
