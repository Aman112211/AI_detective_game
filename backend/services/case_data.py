import json
from collections import Counter
from pathlib import Path
import re


CASE_DIR = Path(__file__).resolve().parent.parent / "data"
DEFAULT_MODE = "pirate"
CASE_FILES = {
    "pirate": CASE_DIR / "mystery-pirate.json",
    "noir": CASE_DIR / "mystery-noir.json",
}
STOP_WORDS = {
    "a",
    "about",
    "and",
    "be",
    "could",
    "did",
    "do",
    "for",
    "from",
    "had",
    "has",
    "have",
    "how",
    "i",
    "in",
    "is",
    "it",
    "me",
    "of",
    "on",
    "or",
    "the",
    "to",
    "was",
    "were",
    "what",
    "when",
    "where",
    "who",
    "why",
    "s",
}


def load_case(mode=None):
    selected_mode = (mode or DEFAULT_MODE).lower()
    path = CASE_FILES.get(selected_mode, CASE_FILES[DEFAULT_MODE])
    with path.open(encoding="utf-8") as case_file:
        return json.load(case_file)


def public_case(case):
    return {
        "mode": case.get("mode", DEFAULT_MODE),
        "title": case["title"],
        "briefing": case["briefing"],
        "setting": case.get("setting", ""),
        "detectiveCharacter": case.get("detectiveCharacter", {}),
        "suspects": [
            {
                "id": suspect["id"],
                "name": suspect["name"],
                "bio": suspect["bio"],
                "motiveHint": suspect["motiveHint"],
                "alibi": suspect["alibi"],
                "initialSuspicion": suspect.get("initialSuspicion", "medium"),
            }
            for suspect in case["suspects"]
        ],
    }


def _words(value):
    return {
        word
        for word in re.findall(r"[a-z0-9]+", value.lower())
        if word not in STOP_WORDS
    }


def _normalized_text(value):
    return re.sub(r"[^a-z0-9]+", " ", str(value).lower()).strip()


def _contains_phrase(text, phrase):
    return _normalized_text(phrase) in _normalized_text(text)


def discover_evidence(case, message, discovered_ids):
    message_words = _words(message)
    normalized_message = _normalized_text(message)
    discovered = set(discovered_ids)
    evidence_items = case.get("evidence", [])
    evidence_discovery = case.get("evidenceDiscovery", {})

    if not evidence_items:
        return []

    candidate_phrases_by_evidence = {}
    word_usage = Counter()

    for evidence in evidence_items:
        evidence_id = evidence.get("id")
        if not evidence_id:
            continue
        phrases = []
        for key in ("description", "pointsTo", "id", "name"):
            value = evidence.get(key)
            if value:
                phrases.append(str(value))

        if isinstance(evidence_discovery, dict):
            rules = evidence_discovery.get(evidence_id, {})
            if isinstance(rules, dict):
                for condition in rules.get("unlockConditions", []):
                    if isinstance(condition, str):
                        phrases.append(str(condition))

        candidate_phrases = set()
        for phrase in phrases:
            cleaned = _normalized_text(phrase)
            words = re.findall(r"[a-z0-9]+", cleaned)
            candidate_phrases.add(cleaned)
            for index in range(len(words)):
                for end in range(index + 1, min(index + 4, len(words)) + 1):
                    candidate_phrases.add(" ".join(words[index:end]))

        candidate_phrases_by_evidence[evidence_id] = candidate_phrases
        for word in _words(" ".join(candidate_phrases)):
            word_usage[word] += 1

    newly_discovered = []
    for evidence in evidence_items:
        evidence_id = evidence.get("id")
        if evidence_id in discovered or not evidence_id:
            continue

        phrase_hits = [
            phrase for phrase in candidate_phrases_by_evidence.get(evidence_id, set())
            if phrase and phrase in normalized_message
        ]
        if phrase_hits:
            newly_discovered.append(evidence_id)
            continue

        distinctive_words = {
            word
            for word in _words(" ".join(candidate_phrases_by_evidence.get(evidence_id, set())))
            if word_usage.get(word, 0) <= 2
        }
        if message_words & distinctive_words:
            newly_discovered.append(evidence_id)

    if newly_discovered:
        return newly_discovered

    evidence_discovery = case.get("evidenceDiscovery", {})
    if isinstance(evidence_discovery, dict):
        for evidence_id, rules in evidence_discovery.items():
            if evidence_id in discovered or not isinstance(rules, dict):
                continue
            conditions = rules.get("unlockConditions", [])
            if isinstance(conditions, list) and any(
                _normalized_text(condition) in normalized_message for condition in conditions
            ):
                newly_discovered.append(evidence_id)

    return newly_discovered


def controlled_context(case, message, discovered_ids):
    message_words = _words(message)
    context = {
        "briefing": case.get("briefing", ""),
        "suspects": [],
        "timeline": {},
        "locations": [],
        "discoveredEvidence": [],
    }

    for suspect in case.get("suspects", []):
        suspect_text = " ".join(
            [suspect["name"], suspect.get("bio", ""), suspect.get("motiveHint", ""), suspect.get("alibi", "")]
        )
        if message_words & _words(suspect_text):
            context["suspects"].append(
                {
                    "name": suspect["name"],
                    "bio": suspect.get("bio", ""),
                    "motiveHint": suspect.get("motiveHint", ""),
                    "alibi": suspect.get("alibi", ""),
                }
            )

    for period, events in case.get("timeline", {}).items():
        if message_words & _words(" ".join(events + [period])):
            context["timeline"][period] = events

    for location in case.get("locations", []):
        location_text = " ".join(
            [location.get("name", ""), location.get("description", "")] + location.get("relevantFacts", [])
        )
        if message_words & _words(location_text):
            context["locations"].append(
                {"name": location.get("name", ""), "description": location.get("description", "")}
            )

    evidence_by_id = {item["id"]: item for item in case.get("evidence", [])}
    for evidence_id in discovered_ids:
        evidence = evidence_by_id.get(evidence_id)
        if evidence:
            context["discoveredEvidence"].append(
                {
                    "id": evidence["id"],
                    "name": evidence.get("name", evidence["id"]),
                    "description": evidence.get("description", ""),
                    "category": evidence.get("category", "general"),
                }
            )

    return context


def public_evidence(case, evidence_ids):
    evidence_by_id = {item["id"]: item for item in case.get("evidence", [])}
    public_items = []
    for evidence_id in evidence_ids:
        evidence = evidence_by_id.get(evidence_id)
        if not evidence:
            continue
        public_items.append(
            {
                "id": evidence["id"],
                "name": evidence.get("name", evidence["id"].replace("_", " ").title()),
                "description": evidence.get("description", ""),
                "category": evidence.get("category", "general"),
                "importance": evidence.get("importance", "medium"),
            }
        )
    return public_items