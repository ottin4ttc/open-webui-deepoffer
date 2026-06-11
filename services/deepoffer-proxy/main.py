from __future__ import annotations

import json
import os
import time
import uuid

import httpx
from fastapi import FastAPI, Request
from fastapi.responses import StreamingResponse

app = FastAPI()

DEEPOFFER_CHAT_COMPLETIONS_URL = os.getenv(
    "DEEPOFFER_CHAT_COMPLETIONS_URL",
    "https://int.ttcadvisory.com/api/llm/deepoffer/v1/chat/completions",
)
DEEPOFFER_API_KEY = os.getenv("DEEPOFFER_API_KEY", "")
DEEPOFFER_OPENAI_MODEL = os.getenv("DEEPOFFER_OPENAI_MODEL", "deepoffer-r1")
DEEPOFFER_UPSTREAM_MODEL = os.getenv(
    "DEEPOFFER_UPSTREAM_MODEL", "deepoffer-r1-32b-202503"
)
STREAM_FLUSH_CHARS = int(os.getenv("STREAM_FLUSH_CHARS", "12"))
STREAM_FLUSH_SECONDS = float(os.getenv("STREAM_FLUSH_SECONDS", "0.08"))
STREAM_FLUSH_PUNCTUATION = set("。！？!?；;\n")


@app.get("/v1/models")
async def list_models():
    return {
        "object": "list",
        "data": [
            {
                "id": DEEPOFFER_OPENAI_MODEL,
                "object": "model",
                "created": 1700000000,
                "owned_by": "ttc",
            }
        ],
    }


def build_upstream_payload(body: dict, stream: bool | None = None) -> dict:
    return {
        "model": DEEPOFFER_UPSTREAM_MODEL,
        "messages": body.get("messages", []),
        "max_tokens": body.get("max_tokens", 1024),
        "stream": body.get("stream", False) if stream is None else stream,
        **({"temperature": body["temperature"]} if "temperature" in body else {}),
        **({"top_p": body["top_p"]} if "top_p" in body else {}),
        **({"stop": body["stop"]} if "stop" in body else {}),
    }


def upstream_headers() -> dict:
    headers = {"Content-Type": "application/json"}

    if DEEPOFFER_API_KEY:
        headers["Authorization"] = (
            DEEPOFFER_API_KEY
            if DEEPOFFER_API_KEY.startswith("Bearer ")
            else f"Bearer {DEEPOFFER_API_KEY}"
        )

    return headers


def normalize_completion(data: dict) -> dict:
    choices = data.get("choices") or []
    if choices:
        content = choices[0].get("message", {}).get("content", "")
        finish_reason = choices[0].get("finish_reason") or "stop"
    else:
        content = data.get("content", "")
        finish_reason = "stop" if content else "error"

    return {
        "id": data.get("id") or f"chatcmpl-{uuid.uuid4().hex[:8]}",
        "object": "chat.completion",
        "created": data.get("created") or int(time.time()),
        "model": DEEPOFFER_OPENAI_MODEL,
        "choices": [
            {
                "index": 0,
                "message": {"role": "assistant", "content": content},
                "finish_reason": finish_reason,
            }
        ],
        "usage": data.get(
            "usage",
            {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0},
        ),
    }


def sse_chunk(content: str = "", finish_reason=None) -> str:
    chunk = {
        "id": f"chatcmpl-{uuid.uuid4().hex[:8]}",
        "object": "chat.completion.chunk",
        "created": int(time.time()),
        "model": DEEPOFFER_OPENAI_MODEL,
        "choices": [
            {
                "index": 0,
                "delta": {"content": content} if content else {},
                "finish_reason": finish_reason,
            }
        ],
    }
    return f"data: {json.dumps(chunk, ensure_ascii=False)}\n\n"


async def stream_single_completion(body: dict):
    try:
        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(
                DEEPOFFER_CHAT_COMPLETIONS_URL,
                json=build_upstream_payload(body, stream=False),
                headers=upstream_headers(),
            )
            data = response.json()
            response.raise_for_status()
            completion = normalize_completion(data)
            content = completion["choices"][0]["message"]["content"]
            if content:
                yield sse_chunk(content)
            yield sse_chunk("", "stop")
            yield "data: [DONE]\n\n"
    except Exception as exc:
        yield sse_chunk(f"DeepOffer upstream error: {exc}", "error")
        yield "data: [DONE]\n\n"


async def stream_response(body: dict):
    try:
        async with httpx.AsyncClient(timeout=120.0) as client:
            async with client.stream(
                "POST",
                DEEPOFFER_CHAT_COMPLETIONS_URL,
                json=build_upstream_payload(body, stream=True),
                headers=upstream_headers(),
            ) as response:
                content_type = response.headers.get("Content-Type", "")
                if response.status_code >= 400:
                    error_text = await response.aread()
                    raise RuntimeError(
                        f"HTTP {response.status_code}: "
                        f"{error_text.decode('utf-8', 'replace')[:500]}"
                    )

                if "text/event-stream" not in content_type:
                    raw = await response.aread()
                    data = json.loads(raw.decode("utf-8", "replace"))
                    completion = normalize_completion(data)
                    content = completion["choices"][0]["message"]["content"]
                    if content:
                        yield sse_chunk(content)
                    yield sse_chunk("", "stop")
                    yield "data: [DONE]\n\n"
                    return

                emitted = False
                buffer = ""
                last_flush = time.monotonic()

                def should_flush(text: str, finish_reason=None) -> bool:
                    if finish_reason:
                        return True
                    if not text:
                        return False
                    if len(text) >= STREAM_FLUSH_CHARS:
                        return True
                    if text[-1] in STREAM_FLUSH_PUNCTUATION:
                        return True
                    return time.monotonic() - last_flush >= STREAM_FLUSH_SECONDS

                async for line in response.aiter_lines():
                    if not line or not line.startswith("data: "):
                        continue

                    data_str = line[6:]
                    if data_str == "[DONE]":
                        if buffer:
                            yield sse_chunk(buffer)
                        yield "data: [DONE]\n\n"
                        return

                    try:
                        data = json.loads(data_str)
                    except json.JSONDecodeError:
                        continue

                    choices = data.get("choices") or []
                    if not choices:
                        continue

                    choice = choices[0]
                    delta = choice.get("delta") or {}
                    content = delta.get("content") or ""
                    finish_reason = choice.get("finish_reason")

                    if content:
                        buffer += content

                    if should_flush(buffer, finish_reason):
                        emitted = True
                        yield sse_chunk(buffer, finish_reason)
                        buffer = ""
                        last_flush = time.monotonic()

                if not emitted:
                    async for chunk in stream_single_completion(body):
                        yield chunk
                else:
                    if buffer:
                        yield sse_chunk(buffer)
                    yield "data: [DONE]\n\n"
    except Exception:
        async for chunk in stream_single_completion(body):
            yield chunk


@app.post("/v1/chat/completions")
async def chat_completions(request: Request):
    body = await request.json()

    if body.get("stream", False):
        return StreamingResponse(stream_response(body), media_type="text/event-stream")

    async with httpx.AsyncClient(timeout=120.0) as client:
        response = await client.post(
            DEEPOFFER_CHAT_COMPLETIONS_URL,
            json=build_upstream_payload(body, stream=False),
            headers=upstream_headers(),
        )
        data = response.json()
        response.raise_for_status()
        return normalize_completion(data)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8301)
