from flask import Blueprint, jsonify, request

from services.case_data import load_case, public_case
from services.session_store import create_session


session_bp = Blueprint("session", __name__)


@session_bp.post("/session")
def start_session():
    payload = request.get_json(silent=True) or {}
    mode = str(payload.get("mode", "pirate") or "pirate").lower()

    case = load_case(mode)
    max_questions = case.get("objective", {}).get("maxQuestions", 15)
    session = create_session(max_questions, mode=mode)
    public_information = public_case(case)

    return jsonify(
        {
            "sessionId": session["sessionId"],
            "mode": public_information["mode"],
            "title": public_information["title"],
            "briefing": public_information["briefing"],
            "setting": public_information["setting"],
            "detectiveCharacter": public_information["detectiveCharacter"],
            "suspects": public_information["suspects"],
            "questionsRemaining": session["questionsRemaining"],
        }
    )