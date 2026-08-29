import json
import os
import traceback
from urllib.request import Request, urlopen

try:
    from google import genai
except Exception:  # pragma: no cover
    genai = None


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


def _build_gemini_url(api_url, model):
    base_url = api_url.rstrip("/")
    lower_url = base_url.lower()
    if "generativelanguage.googleapis.com" in lower_url or "googleapis.com" in lower_url:
        if ":generatecontent" in lower_url:
            return base_url
        if "/models" in lower_url:
            return f"{base_url}/{model}:generateContent"
        return f"{base_url}/{model}:generateContent"
    return api_url


def _extract_gemini_text(result):
    candidates = result.get("candidates") or []
    if not candidates:
        return ""
    parts = candidates[0].get("content", {}).get("parts", [])
    text_parts = []
    for part in parts:
        if isinstance(part, dict):
            text = part.get("text")
            if text:
                text_parts.append(text)
    return "\n".join(text_parts).strip()


def _extract_openai_content(result):
    try:
        choices = result.get("choices") or []
        if not choices:
            return ""
        message = choices[0].get("message") or {}
        content = message.get("content")
        if isinstance(content, list):
            text_parts = []
            for block in content:
                if isinstance(block, dict):
                    text = block.get("text")
                    if text:
                        text_parts.append(text)
            if text_parts:
                return "\n".join(text_parts).strip()
        if isinstance(content, str):
            return content.strip()
    except Exception:
        pass
    return ""


def generate_response(message, context):
    api_key = os.getenv("LLM_API_KEY") or os.getenv("GOOGLE_API_KEY")
    api_url = os.getenv("LLM_API_URL", "https://api.groq.com/openai/v1/chat/completions")
    model = os.getenv("LLM_MODEL", "openai/gpt-oss-20b")
    if not api_key:
        return _fallback_response(message, context)

    try:
        system_prompt = (
            "You are First Mate Salty Sable. Answer in character using only the supplied "
            "case context. Never invent facts, reveal the culprit, mention hidden data, "
            "or state that you are an AI. Keep the answer to 2-4 short sentences."
        )

        if genai is not None:
            client = genai.Client(api_key=api_key)
            response = client.models.generate_content(
                model=model,
                contents=json.dumps({"question": message, "caseContext": context}),
                config={"system_instruction": system_prompt, "temperature": 0},
            )
            return getattr(response, "text", None) or _extract_gemini_text(response.to_dict()) or _fallback_response(message, context)

        is_gemini = bool(api_url and ("generativelanguage.googleapis.com" in api_url.lower() or "googleapis.com" in api_url.lower()))
        if is_gemini:
            request_url = _build_gemini_url(api_url, model)
            payload = json.dumps(
                {
                    "contents": [{"parts": [{"text": json.dumps({"question": message, "caseContext": context})}]}],
                    "systemInstruction": {"parts": [{"text": system_prompt}]},
                    "generationConfig": {"temperature": 0},
                }
            ).encode("utf-8")
            headers = {
                "Content-Type": "application/json",
                "x-goog-api-key": api_key,
            }
        else:
            request_url = api_url
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
            headers = {
                "Authorization": "Bearer " + api_key,
                "Content-Type": "application/json",
            }

        request = Request(request_url, data=payload, headers=headers, method="POST")
        with urlopen(request, timeout=30) as response:
            result = json.load(response)

        if is_gemini:
            return _extract_gemini_text(result) or _fallback_response(message, context)

        text = _extract_openai_content(result)
        if text:
            return text
        return _fallback_response(message, context)
    except Exception as exc:
        print(f"[LLM_ERROR] {type(exc).__name__}: {exc}")
        traceback.print_exc()
        return _fallback_response(message, context)