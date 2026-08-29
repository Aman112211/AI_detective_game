import json
import os
import traceback

from groq import Groq


class LlmError(Exception):
    pass


def _extract_groq_content(result):
    """Accepts either a dict (raw JSON) or a Groq SDK response object."""
    try:
        if hasattr(result, "choices"):
            choices = result.choices or []
            if not choices:
                return ""
            message = choices[0].message
            content = getattr(message, "content", None)
            if isinstance(content, str):
                return content.strip()
            if isinstance(content, list):
                text_parts = []
                for block in content:
                    text = (
                        getattr(block, "text", None)
                        if not isinstance(block, dict)
                        else block.get("text")
                    )
                    if text:
                        text_parts.append(text)
                return "\n".join(text_parts).strip()
            return ""

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
    api_key = (os.getenv("LLM_API_KEY") or os.getenv("GROQ_API_KEY") or "").strip()
    model = os.getenv("LLM_MODEL", "openai/gpt-oss-120b")
    if not api_key:
        raise LlmError("LLM_API_KEY or GROQ_API_KEY is not set")

    system_prompt = (
        "You are First Mate Salty Sable. Answer in character using only the supplied "
        "case context. Never invent facts, reveal the culprit, mention hidden data, "
        "or state that you are an AI. Keep the answer to 2-4 short sentences."
    )

    try:
        user_content = json.dumps({"question": message, "caseContext": context})
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_content},
        ]

        request_kwargs = {
            "model": model,
            "temperature": 0,
            "messages": messages,
        }
        if "gpt-oss" in model.lower():
            request_kwargs["reasoning_effort"] = os.getenv("LLM_REASONING_EFFORT", "medium")

        client = Groq(api_key=api_key)
        result = client.chat.completions.create(**request_kwargs)

        text = _extract_groq_content(result)
        if text:
            return text
        raise LlmError(f"LLM returned an empty response. Raw response: {result}")
    except LlmError:
        raise
    except Exception as exc:
        print(f"[LLM_ERROR] {type(exc).__name__}: {exc}")
        traceback.print_exc()
        raise LlmError(f"{type(exc).__name__}: {exc}") from exc
