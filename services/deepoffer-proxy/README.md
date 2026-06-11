# DeepOffer Proxy

OpenAI-compatible proxy for the DeepOffer LLM service.

It exposes:

- `GET /v1/models`
- `POST /v1/chat/completions`

The production OpenWebUI service points `OPENAI_API_BASE_URL` at this proxy.

## Configuration

Environment variables:

| Variable | Default | Description |
| --- | --- | --- |
| `DEEPOFFER_CHAT_COMPLETIONS_URL` | `https://int.ttcadvisory.com/api/llm/deepoffer/v1/chat/completions` | Upstream DeepOffer chat-completions endpoint. |
| `DEEPOFFER_API_KEY` | empty | Bearer token value or full `Bearer ...` authorization header value for the upstream service. |
| `DEEPOFFER_OPENAI_MODEL` | `deepoffer-r1` | Model ID exposed to OpenWebUI. |
| `DEEPOFFER_UPSTREAM_MODEL` | `deepoffer-r1-32b-202503` | Model ID sent to the upstream service. |
| `STREAM_FLUSH_CHARS` | `12` | Minimum buffered character count before a streamed chunk is flushed. |
| `STREAM_FLUSH_SECONDS` | `0.08` | Maximum buffering time before a streamed chunk is flushed. |

## Local Run

```bash
docker compose up --build
```

Then call:

```bash
curl http://127.0.0.1:8301/v1/models
```
