from flask import Blueprint, jsonify

from services.case_data import load_case, public_case
from services.session_store import create_session


session_bp = Blueprint("session", __name__)


@session_bp.post("/session")
def start_session():
    case = load_case()
    max_questions = case["objective"]["maxQuestions"]
    session = create_session(max_questions)
    public_information = public_case(case)

    return jsonify(
        {
            "sessionId": session["sessionId"],
            "title": public_information["title"],
            "briefing": public_information["briefing"],
            "suspects": public_information["suspects"],
            "questionsRemaining": session["questionsRemaining"],
        }
    )