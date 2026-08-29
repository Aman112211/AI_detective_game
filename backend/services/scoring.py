import re


def _normalized_words(value):
    return set(re.findall(r"[a-z0-9]+", value.lower()))


def _contains_any(value, phrases):
    normalized = value.lower()
    return any(phrase.lower() in normalized for phrase in phrases)


def score_submission(case, submission):
    answer_key = case.get("answerKey", {})
    evidence_ids = submission.get("evidence", [])
    if not isinstance(evidence_ids, list):
        evidence_ids = []

    required_evidence = answer_key.get("requiredEvidenceIds", [])
    minimum_evidence = answer_key.get(
        "minimumEvidenceForCorrectAccusation",
        max(1, len(required_evidence)),
    )

    identity_points = 10 if submission.get("culprit") == answer_key.get("culprit") else 0
    method_points = 5 if _contains_any(
        submission.get("method", ""),
        ["wire", "lock", "porthole", "rowboat", "storm"],
    ) else 0
    motive_points = 5 if _contains_any(
        submission.get("motive", ""),
        ["voss", "rival", "paid", "weaken"],
    ) else 0
    valid_evidence = set(evidence_ids) & set(required_evidence)
    evidence_points = 5 if len(valid_evidence) >= minimum_evidence else 0

    return {
        "score": identity_points + method_points + motive_points + evidence_points,
        "breakdown": {
            "identity": identity_points,
            "method": method_points,
            "motive": motive_points,
            "evidence": evidence_points,
        },
    }