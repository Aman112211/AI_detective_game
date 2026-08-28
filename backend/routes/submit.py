from flask import Blueprint, jsonify, request

from services.case_data import load_case
from services.scoring import score_submission
from services.session_store import get_session


submit_bp = Blueprint("submit", __name__)


@submit_bp.post("/submit")
def submit_accusation():
    payload = request.get_json(silent=True) or {}
    session_id = payload.get("sessionId")
    if not isinstance(session_id, str) or not session_id:
        return jsonify({"error": "A valid sessionId is required"}), 400

    session = get_session(session_id)
    if session is None:
        return jsonify({"error": "Session not found"}), 404

    session["accusationAttempts"] += 1
    result = score_submission(load_case(), payload)
    if result["score"] == 25:
        session["gameStatus"] = "solved"

    return jsonify(
        {
            "score": result["score"],
            "breakdown": result["breakdown"],
            "gameStatus": session["gameStatus"],
        }
    )