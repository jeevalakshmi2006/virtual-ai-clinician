"""
Safety Layer
------------
This module runs BEFORE the LLM sees any message. If a user mentions a
red-flag symptom combination, we short-circuit the entire pipeline and
return an emergency instruction immediately. We never let the language
model be the last line of defense for a life-threatening symptom.
"""

RED_FLAG_PHRASES = [
    "chest pain", "chest pressure", "chest tightness",
    "can't breathe", "cant breathe", "can not breathe",
    "difficulty breathing", "shortness of breath", "gasping for air",
    "slurred speech", "face drooping", "facial drooping",
    "sudden confusion", "sudden weakness", "arm weakness",
    "severe bleeding", "won't stop bleeding", "wont stop bleeding",
    "loss of consciousness", "passed out", "fainted and won't wake",
    "suicidal", "suicide", "want to end my life", "self harm", "self-harm",
    "seizure", "convulsion",
    "blue lips", "turning blue",
    "severe allergic reaction", "throat swelling", "swelling of throat",
    "worst headache of my life",
    "coughing blood", "vomiting blood",
]

EMERGENCY_MESSAGE = (
    "This may describe a medical emergency. Please call your local emergency "
    "number or go to the nearest emergency room right now. This assistant is "
    "not able to safely continue triage for symptoms like this — please seek "
    "immediate in-person medical care."
)


def check_red_flags(user_text: str) -> dict:
    """Scan raw user text for emergency-indicating phrases."""
    text = user_text.lower()
    matched = [phrase for phrase in RED_FLAG_PHRASES if phrase in text]

    if matched:
        return {
            "emergency": True,
            "matched_terms": matched,
            "message": EMERGENCY_MESSAGE,
        }

    return {"emergency": False, "matched_terms": [], "message": None}
