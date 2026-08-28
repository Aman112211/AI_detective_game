import json
import os
from urllib.request import Request, urlopen


def _fallback_response(message, context):
    details = []
    details.extend(suspect["alibi"] for suspect in context["suspects"])
    details.extend(
        event
        for events in context["timeline"].values()
        for event in events
    )
    details.extend(evidence["description"] for evidence in context["discoveredEvidence"])

    if not details:
        return "Ask me about a suspect, the evidence, the timeline, or a place aboard the ship, detective."
    return "Aye, detective. " + " ".join(details[:3])


def generate_response(message, context):
    api_key = os.getenv("LLM_API_KEY")
    api_url = os.getenv("LLM_API_URL", "https://api.openai.com/v1/chat/completions")
    model = os.getenv("LLM_MODEL", "gpt-4o-mini")
    if not api_key:
        return _fallback_response(message, context)

    system_prompt = (
        "You are First Mate Salty Sable. Answer in character using only the supplied "
        "case context. Never invent facts, reveal the culprit, mention hidden data, "
        "or state that you are an AI. Keep the answer to 2-4 short sentences."
    )
    payload = json.dumps(
        {
            "model": model,
            "temperature": 0,
            "messages": [
                {"role": "system", "content": system_prompt},
                {
                    "role": "user",
                    "content": json.dumps({"question": message, "caseContext": context}),
                },
            ],
        }
    ).encode("utf-8")
    request = Request(
        api_url,
        data=payload,
        headers={
            "Authorization": "Bearer " + api_key,
            "Content-Type": "application/json",
        },
        method="POST",
    )
    with urlopen(request, timeout=30) as response:
        result = json.load(response)
    return result["choices"][0]["message"]["content"]