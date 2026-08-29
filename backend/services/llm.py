import json
import os
import traceback
from urllib.error import HTTPError
from urllib.request import Request, urlopen

try:
    from google import genai
except Exception:  # pragma: no cover
    genai = None

try:
    from groq import Groq
except Exception:  # pragma: no cover
    Groq = None


class LlmError(Exception):
    pass


def _is_gemini_url(api_url):
    lower_url = api_url.lower()
    return "generativelanguage.googleapis.com" in lower_url or "googleapis.com" in lower_url


def _resolve_llm_config():
    api_url = os.getenv("LLM_API_URL", "https://api.groq.com/openai/v1/chat/completions")
    model = os.getenv("LLM_MODEL", "openai/gpt-oss-120b")
    llm_key = (os.getenv("LLM_API_KEY") or os.getenv("GROQ_API_KEY") or "").strip()
    google_key = (os.getenv("GOOGLE_API_KEY") or "").strip()
    is_gemini = _is_gemini_url(api_url)

    if is_gemini:
        api_key = google_key or llm_key
        if not api_key:
            raise LlmError(
                "GOOGLE_API_KEY (or LLM_API_KEY) is not set for the Gemini API."
            )
    else:
        if not llm_key and google_key:
            raise LlmError(
                "Only GOOGLE_API_KEY is set, but the configured provider is Groq. "
                "Set LLM_API_KEY (or GROQ_API_KEY) to your Groq API key, or change "
                "LLM_API_URL to https://generativelanguage.googleapis.com/v1beta/models "
                "and LLM_MODEL to a Gemini model (for example gemini-2.0-flash)."
            )
        api_key = llm_key
        if not api_key:
            raise LlmError("LLM_API_KEY or GROQ_API_KEY is not set")

    return api_key, api_url, model, is_gemini


def _format_http_error(exc):
    body = ""
    try:
        raw = exc.read()
        if raw:
            body = raw.decode("utf-8", errors="replace").strip()
    except Exception:
        pass

    message = f"HTTP {exc.code} {exc.reason} from {exc.url}"
    if body:
        message += f": {body}"
    return message


def _build_gemini_url(api_url, model):
    base_url = api_url.rstrip("/")
    lower_url = base_url.lower()
    if _is_gemini_url(lower_url):
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


def _generate_groq_response(api_key, model, system_prompt, message, context):
    if Groq is None:
        raise LlmError("The groq package is not installed. Add groq to backend/requirements.txt.")

    client = Groq(api_key=api_key)
    request_kwargs = {
        "model": model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {
                "role": "user",
                "content": json.dumps({"question": message, "caseContext": context}),
            },
        ],
        "temperature": 0,
    }

    if "gpt-oss" in model.lower():
        request_kwargs["reasoning_effort"] = os.getenv("LLM_REASONING_EFFORT", "medium")

    completion = client.chat.completions.create(**request_kwargs)
    text = (completion.choices[0].message.content or "").strip()
    if not text:
        raise LlmError(f"LLM returned an empty response. Raw response: {completion}")
    return text


def _generate_gemini_response(api_key, api_url, model, system_prompt, message, context):
    if genai is not None:
        client = genai.Client(api_key=api_key)
        response = client.models.generate_content(
            model=model,
            contents=json.dumps({"question": message, "caseContext": context}),
            config={"system_instruction": system_prompt, "temperature": 0},
        )
        text = getattr(response, "text", None) or _extract_gemini_text(response.to_dict())
        if not text:
            raise LlmError(f"LLM returned an empty response. Raw response: {response.to_dict()}")
        return text

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

    request = Request(request_url, data=payload, headers=headers, method="POST")
    with urlopen(request, timeout=30) as response:
        result = json.load(response)

    text = _extract_gemini_text(result)
    if not text:
        raise LlmError(f"LLM returned an empty response. Raw response: {result}")
    return text


def generate_response(message, context):
    api_key, api_url, model, is_gemini = _resolve_llm_config()

    system_prompt = (
        "You are First Mate Salty Sable. Answer in character using only the supplied "
        "case context. Never invent facts, reveal the culprit, mention hidden data, "
        "or state that you are an AI. Keep the answer to 2-4 short sentences."
    )

    try:
        if is_gemini:
            return _generate_gemini_response(
                api_key, api_url, model, system_prompt, message, context
            )
        return _generate_groq_response(api_key, model, system_prompt, message, context)
    except LlmError:
        raise
    except HTTPError as exc:
        print(f"[LLM_ERROR] {_format_http_error(exc)}")
        traceback.print_exc()
        raise LlmError(_format_http_error(exc)) from exc
    except Exception as exc:
        print(f"[LLM_ERROR] {type(exc).__name__}: {exc}")
        traceback.print_exc()
        raise LlmError(f"{type(exc).__name__}: {exc}") from exc
