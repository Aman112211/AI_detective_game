from uuid import uuid4


SESSIONS = {}


def create_session(max_questions, mode="pirate"):
    session_id = str(uuid4())
    session = {
        "sessionId": session_id,
        "mode": mode,
        "questionsRemaining": max_questions,
        "questionsAsked": 0,
        "askedQuestions": [],
        "discoveredEvidenceIds": [],
        "accusationAttempts": 0,
        "gameStatus": "investigating",
    }
    SESSIONS[session_id] = session
    return session


def get_session(session_id):
    return SESSIONS.get(session_id)