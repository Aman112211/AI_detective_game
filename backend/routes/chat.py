from flask import Blueprint, jsonify, request

from services.case_data import (
    controlled_context,
    discover_evidence,
    load_case,
    public_evidence,
)
from services.llm import LlmError, generate_response
from services.session_store import get_session


chat_bp = Blueprint("chat", __name__)


@chat_bp.post("/chat")
def chat():
    payload = request.get_json(silent=True) or {}
    session_id = payload.get("sessionId")
    message = payload.get("message")

    if not isinstance(session_id, str) or not session_id:
        return jsonify({"error": "A valid sessionId is required"}), 400
    if not isinstance(message, str) or not message.strip():
        return jsonify({"error": "A non-empty message is required"}), 400

    session = get_session(session_id)
    if session is None:
        return jsonify({"error": "Session not found"}), 404
    if session["gameStatus"] != "investigating":
        return jsonify({"error": "This session is not available for questions"}), 409
    if session["questionsRemaining"] <= 0:
        return jsonify({"error": "No questions remaining"}), 409

    case = load_case(session.get("mode", "pirate"))
    message = message.strip()
    new_evidence_ids = discover_evidence(
        case, message, session["discoveredEvidenceIds"]
    )
    all_discovered_ids = session["discoveredEvidenceIds"] + new_evidence_ids
    context = controlled_context(case, message, all_discovered_ids)

    try:
        response_text = generate_response(message, context)
    except LlmError as exc:
        return jsonify({"error": str(exc)}), 502

    session["questionsRemaining"] -= 1
    session["questionsAsked"] += 1
    session["askedQuestions"].append(message)
    session["discoveredEvidenceIds"].extend(new_evidence_ids)

    return jsonify(
        {
            "response": response_text,
            "questionsRemaining": session["questionsRemaining"],
            "newEvidence": public_evidence(case, new_evidence_ids),
            "discoveredEvidenceIds": new_evidence_ids,
            "gameStatus": session["gameStatus"],
        }
    )
