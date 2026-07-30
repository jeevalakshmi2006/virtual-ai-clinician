import json
import os
import re
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from prompts import SYSTEM_PROMPT
from retrieval import retriever
from safety import check_red_flags

load_dotenv()

API_KEY = os.getenv("GROQ_API_KEY", "")
MODEL_NAME = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")

app = FastAPI(title="Virtual AI Clinician API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


class ChatMessage(BaseModel):
    role: str
    content: str


class ChatRequest(BaseModel):
    message: str
    history: list[ChatMessage] = []


def build_reference_context(matches: list[dict]) -> str:
    if not matches:
        return "No closely matching reference conditions were found."
    lines = []
    for m in matches:
        lines.append(
            f"- {m['condition']} (relevance {m['relevance_score']}): "
            f"symptoms: {m['symptoms']}. triage_level: {m['triage_level']}. "
            f"advice: {m['advice']}. medicine_category: {m['medicine_category']}. "
            f"see_doctor_if: {m['see_doctor_if']}."
        )
    return "\n".join(lines)


def extract_json(raw_text: str) -> dict:
    """LLMs sometimes wrap JSON in prose or code fences — extract defensively."""
    cleaned = raw_text.strip()
    cleaned = re.sub(r"^```json\s*|^```\s*|```$", "", cleaned, flags=re.MULTILINE).strip()
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", cleaned, flags=re.DOTALL)
        if match:
            try:
                return json.loads(match.group(0))
            except json.JSONDecodeError:
                pass
    return {
        "follow_up_question": None,
        "possible_conditions": [],
        "triage_level": None,
        "advice": raw_text,
        "medicine_category": None,
        "reasoning": "The assistant's response could not be parsed as structured data.",
        "disclaimer": "This is not a medical diagnosis. Please consult a doctor for confirmation.",
    }


@app.get("/api/health")
def health():
    return {"status": "ok", "api_key_configured": bool(API_KEY)}


@app.post("/api/chat")
def chat(req: ChatRequest):
    # 1. Safety layer runs first, before the LLM ever sees the message
    safety_result = check_red_flags(req.message)
    if safety_result["emergency"]:
        return {
            "emergency": True,
            "response": {
                "advice": safety_result["message"],
                "triage_level": "emergency",
                "possible_conditions": [],
                "medicine_category": None,
                "follow_up_question": None,
                "reasoning": f"Matched red-flag terms: {', '.join(safety_result['matched_terms'])}",
                "disclaimer": "This is not a medical diagnosis. Please consult a doctor for confirmation.",
            },
        }

    if not API_KEY:
        return {
            "emergency": False,
            "response": {
                "advice": "Server is missing a GROQ_API_KEY. Add it to backend/.env and restart the server.",
                "triage_level": None,
                "possible_conditions": [],
                "medicine_category": None,
                "follow_up_question": None,
                "reasoning": "Configuration error.",
                "disclaimer": "This is not a medical diagnosis. Please consult a doctor for confirmation.",
            },
        }

    # 2. Retrieve grounding context from the curated dataset
    matches = retriever.retrieve(req.message)
    context_block = build_reference_context(matches)

    # 3. Call the LLM (Groq) with system prompt + retrieved context + history
    from groq import Groq

    client = Groq(api_key=API_KEY)

    messages = [
        {
            "role": "system",
            "content": SYSTEM_PROMPT
            + f"\n\nREFERENCE CONTEXT (retrieved from dataset):\n{context_block}",
        }
    ]
    for m in req.history:
        messages.append({"role": m.role, "content": m.content})
    messages.append({"role": "user", "content": req.message})

    response = client.chat.completions.create(
        model=MODEL_NAME,
        messages=messages,
        max_tokens=600,
        response_format={"type": "json_object"},
    )

    raw_text = response.choices[0].message.content
    parsed = extract_json(raw_text)

    return {"emergency": False, "response": parsed}


# Serve the frontend as static files, mounted last so /api routes take priority
frontend_dir = Path(__file__).parent.parent / "frontend"
app.mount("/", StaticFiles(directory=str(frontend_dir), html=True), name="frontend")
