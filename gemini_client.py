"""Gọi Gemini qua endpoint OpenAI-compatible. Tối ưu tốc độ, giới hạn độ dài, báo lỗi rõ ràng."""
import json
import os
import requests

GEMINI_BASE_URL = os.getenv("STUDYBOT_BASE_URL", "https://generativelanguage.googleapis.com/v1beta/openai/")
DEFAULT_MODEL = os.getenv("STUDYBOT_MODEL", "gemini-flash-latest")
FALLBACK_MODEL = os.getenv("STUDYBOT_FALLBACK_MODEL", "gemini-flash-lite-latest")

REQUEST_TIMEOUT = (10, 60)
MAX_OUTPUT_TOKENS = 1500

SYSTEM_PROMPT = (
    "Bạn là StudyBot, trợ lý học tập thân thiện cho học sinh. "
    "QUY TẮC NGÔN NGỮ (BẮT BUỘC): Luôn tuân thủ 'INTERFACE LANGUAGE' được chỉ định bên dưới. "
    "Nếu interface là tiếng Việt → trả lời tiếng Việt. "
    "Nếu interface là tiếng Anh → trả lời tiếng Anh. "
    "Không được tự động chuyển sang ngôn ngữ khác dù người dùng viết ngôn ngữ nào. "
    "Trả lời NGẮN GỌN, đi thẳng vào trọng tâm, không lan man, không lặp lại câu hỏi. "
    "Nếu giải bài: trình bày từng bước rõ ràng nhưng súc tích, nêu kết luận cuối cùng. "
    "Dùng Markdown; công thức toán trong $...$ (LaTeX). "
    "Tuyệt đối không bịa thông tin."
)

_FALLBACK_STATUS = {404, 429, 500, 502, 503, 504}


def _headers(key):
    return {"Authorization": f"Bearer {key}", "Content-Type": "application/json"}


def explain_error(r):
    hints = {
        400: "Yêu cầu không hợp lệ (kiểm tra tên Model).",
        401: "API key không đúng hoặc đã bị thu hồi.",
        403: "API key không có quyền hoặc bị chặn khu vực.",
        404: "Không tìm thấy model. Hãy thử model khác.",
        429: "Vượt giới hạn gọi API (quota). Hãy chờ 1 phút rồi thử lại.",
        500: "Server Gemini lỗi, thử lại sau.",
        503: "Gemini đang quá tải, thử lại sau.",
    }
    hint = hints.get(r.status_code, "Lỗi không xác định từ Gemini.")
    r.encoding = "utf-8"
    return f"HTTP {r.status_code}: {hint} Chi tiết: {r.text[:300]}"


def _stream_once(url, key, payload):
    with requests.post(url, headers=_headers(key), json=payload,
                       stream=True, timeout=REQUEST_TIMEOUT) as r:
        if not r.ok:
            raise RuntimeError(explain_error(r))
        for raw in r.iter_lines():
            if not raw:
                continue
            line = raw.decode("utf-8", errors="replace")
            if not line.startswith("data:"):
                continue
            data = line[5:].strip()
            if data == "[DONE]":
                break
            try:
                chunk = json.loads(data)
            except ValueError:
                continue
            choices = chunk.get("choices") or []
            if choices:
                text = (choices[0].get("delta") or {}).get("content")
                if text:
                    yield text


def stream_chat(messages, key, base_url, model, temperature=0.4, system=SYSTEM_PROMPT):
    url = base_url.rstrip("/") + "/chat/completions"
    payload = {
        "model": model,
        "messages": [{"role": "system", "content": system}] + messages,
        "temperature": temperature,
        "max_tokens": MAX_OUTPUT_TOKENS,
        "stream": True,
    }

    try:
        yield from _stream_once(url, key, payload)
        return
    except requests.exceptions.Timeout:
        raise RuntimeError("⏱️ Quá thời gian chờ (Timeout). Mạng có thể đang chậm, vui lòng thử lại.")
    except RuntimeError as e:
        msg = str(e)
        if not any(f"HTTP {code}" in msg for code in _FALLBACK_STATUS):
            raise
        if not FALLBACK_MODEL or FALLBACK_MODEL == model:
            raise

    payload["model"] = FALLBACK_MODEL
    try:
        yield from _stream_once(url, key, payload)
    except Exception as e2:
        raise RuntimeError(f"⚠️ Lỗi API (đã thử fallback): {str(e2)}")