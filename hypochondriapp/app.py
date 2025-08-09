import os
import random
import re
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

import requests
from flask import Flask, jsonify, redirect, render_template, request, url_for


@dataclass
class DiagnosisResult:
    worst_disease_label: str
    severity_score: int
    personality_score: int
    is_dead: bool
    afterlife: Optional[str]
    llm_text: Optional[str]


def create_app() -> Flask:
    app = Flask(__name__)

    @app.get("/")
    def index() -> str:
        return render_template("index.html")

    @app.post("/diagnose")
    def diagnose() -> str:
        symptoms_text: str = request.form.get("symptoms", "").strip()
        quiz_answers = _extract_quiz_answers(request)

        severity_score = compute_symptom_severity(symptoms_text)
        personality_score = compute_personality_score(quiz_answers)

        worst_disease_label = compute_worst_disease_label(symptoms_text, severity_score)
        is_dead, afterlife = compute_death_and_afterlife(severity_score, personality_score)

        llm_text = try_llm_augmented_response(
            symptoms_text=symptoms_text,
            worst_disease_label=worst_disease_label,
            severity_score=severity_score,
            personality_score=personality_score,
            is_dead=is_dead,
            afterlife=afterlife,
        )

        result = DiagnosisResult(
            worst_disease_label=worst_disease_label,
            severity_score=severity_score,
            personality_score=personality_score,
            is_dead=is_dead,
            afterlife=afterlife,
            llm_text=llm_text,
        )

        return render_template("result.html", result=result)

    @app.get("/api/health")
    def api_health() -> Tuple[str, int, Dict[str, str]]:
        return jsonify({"ok": True}), 200, {"Content-Type": "application/json"}

    return app


def _extract_quiz_answers(req: request) -> Dict[str, int]:
    keys = [
        "q_ego",
        "q_empathy",
        "q_impulsivity",
        "q_honesty",
        "q_patience",
    ]
    answers: Dict[str, int] = {}
    for key in keys:
        try:
            answers[key] = int(req.form.get(key, "3"))
        except ValueError:
            answers[key] = 3
    return answers


def compute_symptom_severity(symptoms_text: str) -> int:
    if not symptoms_text:
        return 5

    text = symptoms_text.lower()

    keyword_weights: Dict[str, int] = {
        # Respiratory
        r"shortness of breath|can\'t breathe|difficulty breathing|dyspnea": 35,
        r"chest pain|tightness": 30,
        r"high fever|fever": 20,
        r"coughing blood|hemoptysis": 45,
        # Neuro
        r"seizure|convulsion": 40,
        r"numbness|tingling|weakness one side|facial droop": 45,
        r"confusion|disoriented|fainting|syncope": 25,
        # GI
        r"bloody stool|black tarry stool|vomiting blood": 45,
        r"abdominal pain|severe stomach pain": 20,
        # General
        r"unintentional weight loss|night sweats": 25,
        r"rash|hives": 10,
        r"headache|migraine": 10,
        r"nausea|vomit|diarrhea": 10,
    }

    score = 0
    for pattern, weight in keyword_weights.items():
        if re.search(pattern, text):
            score += weight

    # Length-based bump
    token_count = len(re.findall(r"\w+", text))
    score += min(token_count // 5, 20)

    # Cap the severity to a range 0-100
    return max(0, min(score, 100))


def compute_personality_score(answers: Dict[str, int]) -> int:
    # Likert 1 (best) to 5 (worst). Some items reverse-scored.
    ego = answers.get("q_ego", 3)  # higher worse
    empathy = answers.get("q_empathy", 3)  # higher better (reverse)
    impulsivity = answers.get("q_impulsivity", 3)  # higher worse
    honesty = answers.get("q_honesty", 3)  # higher better (reverse)
    patience = answers.get("q_patience", 3)  # higher better (reverse)

    reverse = lambda x: 6 - x

    weighted = (
        2 * ego
        + 2 * impulsivity
        + reverse(empathy)
        + reverse(honesty)
        + reverse(patience)
    )

    # Normalize roughly to 0-100
    normalized = int((weighted - 5) * (100 / 15))
    return max(0, min(normalized, 100))


def compute_worst_disease_label(symptoms_text: str, severity_score: int) -> str:
    # A tongue-in-cheek mapping yielding overly dramatic worst-case outcomes
    mappings: List[Tuple[str, str]] = [
        (r"chest", "Acute Spontaneous Doomful Cardio Annihilation Syndrome"),
        (r"breath|dyspnea", "Catastrophic Respiratory Collapse of Infinite Despair"),
        (r"headache|migraine", "Explosive Cranial Cataclysmic Pressure Event"),
        (r"fever|sweat", "Hyperthermic Pyroplague of Relentless Combustion"),
        (r"rash|hives|itch", "Dermal Dragon Scales Variant X"),
        (r"stool|vomit|abdomen|diarrhea|nausea", "Gastrointestinal Black Hole Syndrome"),
    ]

    text = symptoms_text.lower()
    for pattern, label in mappings:
        if re.search(pattern, text):
            return label

    if severity_score >= 70:
        return "Stage Omega Multisystem Unraveling"
    if severity_score >= 40:
        return "Prodromal Accelerated Organ Existentialism"
    return "Mildly Concerning But Definitely Terminal Flu-like Entity"


def compute_death_and_afterlife(severity_score: int, personality_score: int) -> Tuple[bool, Optional[str]]:
    # Probability of "death" rises with both severity and worse personality.
    # Keep it tongue-in-cheek; non-graphic and purely fictional.
    death_probability = min(0.9, 0.2 + 0.006 * severity_score + 0.004 * personality_score)
    is_dead = random.random() < death_probability

    if not is_dead:
        return False, None

    # "Heaven" if personality better (lower score); otherwise "Hell".
    afterlife = "heaven" if personality_score < 50 else "hell"
    return True, afterlife


def try_llm_augmented_response(
    symptoms_text: str,
    worst_disease_label: str,
    severity_score: int,
    personality_score: int,
    is_dead: bool,
    afterlife: Optional[str],
) -> Optional[str]:
    if os.getenv("DISABLE_LLM", "0") == "1":
        return None

    ollama_url = os.getenv("OLLAMA_URL", "http://localhost:11434")
    model_name = os.getenv("OLLAMA_MODEL", "mistral")

    if not _ollama_is_available(ollama_url):
        return None

    prompt = build_prompt(
        symptoms_text=symptoms_text,
        worst_disease_label=worst_disease_label,
        severity_score=severity_score,
        personality_score=personality_score,
        is_dead=is_dead,
        afterlife=afterlife,
    )

    try:
        resp = requests.post(
            f"{ollama_url}/api/generate",
            json={
                "model": model_name,
                "prompt": prompt,
                "stream": False,
                "options": {"temperature": 0.9, "top_p": 0.95},
            },
            timeout=30,
        )
        resp.raise_for_status()
        data = resp.json()
        return data.get("response")
    except Exception:
        return None


def build_prompt(
    symptoms_text: str,
    worst_disease_label: str,
    severity_score: int,
    personality_score: int,
    is_dead: bool,
    afterlife: Optional[str],
) -> str:
    style = (
        "You are Hypochondriapp, a theatrical, over-the-top worst-case-scenario health oracle. "
        "You exaggerate in a playful, satirical tone (non-graphic, no medical advice). "
        "Be witty and concise (120-180 words)."
    )

    status = (
        f"Symptoms: {symptoms_text or 'None provided'}\n"
        f"Computed worst diagnosis: {worst_disease_label}\n"
        f"Severity score: {severity_score}/100\n"
        f"Personality severity: {personality_score}/100\n"
        f"Outcome: {'DEAD' if is_dead else 'ALIVE'}{' -> ' + afterlife.upper() if afterlife else ''}"
    )

    instructions = (
        "Requirements:\n"
        "- Open with a dramatic one-line headline about the diagnosis.\n"
        "- Provide a short, humorous explanation of why the symptoms point to this worst-case.\n"
        "- Add a playful roast tied to personality score (higher score = harsher roast, but keep it light).\n"
        "- If DEAD, add a whimsical epilogue for the afterlife destination (heaven or hell).\n"
        "- End with a clear disclaimer: ‘This is satire, not medical advice.’"
    )

    return f"{style}\n\n{status}\n\n{instructions}"


def _ollama_is_available(ollama_url: str) -> bool:
    try:
        resp = requests.get(f"{ollama_url}/api/tags", timeout=3)
        return resp.status_code == 200
    except Exception:
        return False


if __name__ == "__main__":
    app = create_app()
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", "5000")), debug=True)