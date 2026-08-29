import json
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
MIN_SINGLE_TRIGGER_LENGTH = 4


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
        for word in re.findall(r"[a-z0-9]+", str(value).lower())
        if word not in STOP_WORDS
    }


def _normalized_text(value):
    text = str(value).lower()
    text = re.sub(r"'s\b", "", text)
    text = re.sub(r"s'\b", "s", text)
    return re.sub(r"[^a-z0-9]+", " ", text).strip()


def _message_word_list(message):
    return _normalized_text(message).split()


def _phrase_matches_message(message, phrase):
    normalized_phrase = _normalized_text(phrase)
    if not normalized_phrase:
        return False

    phrase_words = normalized_phrase.split()
    message_words = _message_word_list(message)
    if not message_words:
        return False

    if len(phrase_words) == 1:
        word = phrase_words[0]
        if len(word) < MIN_SINGLE_TRIGGER_LENGTH or word in STOP_WORDS:
            return False
        return word in message_words

    for index in range(len(message_words) - len(phrase_words) + 1):
        if message_words[index : index + len(phrase_words)] == phrase_words:
            return True
    return False


def _trigger_phrases_for_evidence(evidence_id, rules):
    if not isinstance(rules, dict):
        return []

    trigger_phrases = rules.get("triggerPhrases", [])
    if isinstance(trigger_phrases, list):
        return [str(phrase) for phrase in trigger_phrases if phrase]

    return []


def discover_evidence(case, message, discovered_ids):
    discovered = set(discovered_ids)
    evidence_discovery = case.get("evidenceDiscovery", {})
    if not isinstance(evidence_discovery, dict):
        return []

    newly_discovered = []
    for evidence in case.get("evidence", []):
        evidence_id = evidence.get("id")
        if not evidence_id or evidence_id in discovered:
            continue

        rules = evidence_discovery.get(evidence_id, {})
        trigger_phrases = _trigger_phrases_for_evidence(evidence_id, rules)
        if not trigger_phrases:
            continue

        if any(_phrase_matches_message(message, phrase) for phrase in trigger_phrases):
            newly_discovered.append(evidence_id)

    return newly_discovered


def controlled_context(case, message, discovered_ids, context_evidence_ids=None):
    message_words = _words(message)
    evidence_ids_for_context = (
        context_evidence_ids if context_evidence_ids is not None else discovered_ids
    )
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
    for evidence_id in evidence_ids_for_context:
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
