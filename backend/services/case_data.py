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


def discover_evidence(case, message, discovered_ids):
    message_words = _words(message)
    discovered = set(discovered_ids)
    newly_discovered = []
    condition_words_by_evidence = {
        evidence_id: {
            word
            for condition in evidence_rules["unlockConditions"]
            for word in _words(condition)
        }
        for evidence_id, evidence_rules in case["evidenceDiscovery"].items()
    }
    word_usage = {}
    for words in condition_words_by_evidence.values():
        for word in words:
            word_usage[word] = word_usage.get(word, 0) + 1

    for evidence_id in case["evidenceDiscovery"]:
        if evidence_id in discovered:
            continue
        distinctive_words = {
            word
            for word in condition_words_by_evidence[evidence_id]
            if word_usage[word] == 1
        }
        if message_words & distinctive_words:
            newly_discovered.append(evidence_id)

    return newly_discovered


def controlled_context(case, message, discovered_ids):
    message_words = _words(message)
    context = {
        "briefing": case["briefing"],
        "suspects": [],
        "timeline": {},
        "locations": [],
        "discoveredEvidence": [],
    }

    for suspect in case["suspects"]:
        suspect_text = " ".join(
            [suspect["name"], suspect["bio"], suspect["motiveHint"], suspect["alibi"]]
        )
        if message_words & _words(suspect_text):
            context["suspects"].append(
                {
                    "name": suspect["name"],
                    "bio": suspect["bio"],
                    "motiveHint": suspect["motiveHint"],
                    "alibi": suspect["alibi"],
                }
            )

    for period, events in case["timeline"].items():
        if message_words & _words(" ".join(events + [period])):
            context["timeline"][period] = events

    for location in case["locations"]:
        location_text = " ".join(
            [location["name"], location["description"]] + location["relevantFacts"]
        )
        if message_words & _words(location_text):
            context["locations"].append(
                {"name": location["name"], "description": location["description"]}
            )

    evidence_by_id = {item["id"]: item for item in case["evidence"]}
    for evidence_id in discovered_ids:
        evidence = evidence_by_id.get(evidence_id)
        if evidence:
            context["discoveredEvidence"].append(
                {
                    "id": evidence["id"],
                    "name": evidence["name"],
                    "description": evidence["description"],
                    "category": evidence["category"],
                }
            )

    return context


def public_evidence(case, evidence_ids):
    evidence_by_id = {item["id"]: item for item in case["evidence"]}
    return [
        {
            "id": evidence_by_id[evidence_id]["id"],
            "name": evidence_by_id[evidence_id]["name"],
            "description": evidence_by_id[evidence_id]["description"],
            "category": evidence_by_id[evidence_id]["category"],
            "importance": evidence_by_id[evidence_id]["importance"],
        }
        for evidence_id in evidence_ids
        if evidence_id in evidence_by_id
    ]