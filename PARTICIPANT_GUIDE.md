# Operational Agent API — Participant Guide

## What you will learn

This demo turns an agent into an API service that a frontend, another agent, a workflow, or a command-line client can call. It introduces the operational wrapper needed around an LLM agent: request validation, routing, session memory, logging, tracing and error responses.

## Why use FastAPI?

| FastAPI capability | What it means in this demo |
|---|---|
| Fast ASGI framework | It handles concurrent web requests efficiently and works well for I/O-heavy agent calls. |
| Defined endpoints | `GET /health` and `POST /chat` become a clear contract that a React frontend, mobile app, workflow or another agent can use. |
| `async def` support | While the application waits for I/O such as an LLM or database call, the server can handle other requests. `async` does not make the LLM itself faster. |
| Automatic API documentation | Open `/docs` to use Swagger UI and try the endpoints without building a frontend. |
| Pydantic validation | The `AgentRequest` and `AgentResponse` models validate request data and document the expected JSON shape. Invalid input receives a useful `422` response automatically. |
| HTTP exception handling | `HTTPException` returns an appropriate HTTP error response instead of exposing an internal Python failure to the client. |
| Middleware | The API adds a request ID, measures request time and creates structured logs for every request. |

FastAPI is a good API layer for an agentic application. It does not replace the agent framework, vector database, frontend, monitoring platform or cloud host.

## What happens when a user sends a query?

1. A client sends JSON to `POST /chat`.
2. Pydantic validates `query` and the optional `session_id`.
3. Middleware assigns a request ID and starts latency measurement.
4. The router selects a low-cost rule path or the LLM agent path.
5. The response, session ID, route and latency are returned as JSON.
6. Logs and optional LangSmith traces help diagnose the interaction.

## Key files

| File or folder | Learner view |
|---|---|
| `app/main.py` | Defines the FastAPI app, endpoints, Pydantic request/response models, middleware and exception handling. |
| `app/core/agent.py` | Configures the Vocareum/OpenAI-compatible model and creates the agent response. |
| `app/core/router.py` | Sends simple operational questions through a deterministic rule path. |
| `app/core/memory.py` | Keeps demo conversation history in memory. Production systems would use Redis or a database. |
| `app/observability/` | Structured logging and optional LangSmith tracing. |
| `demo_client.py` | Calls the API like an external frontend or service would. |
| `verify.py` | Checks routing and memory without starting the API server or calling the LLM. |
| `.env` | Your local configuration. Never commit or share its keys. |

## Configuration

Copy values into `.env` using the same Vocareum style as recent course demos:

```env
OPENAI_API_KEY=your_vocareum_key
OPENAI_BASE_URL=https://your-vocareum-openai-compatible-endpoint/v1
OPENAI_MODEL=gpt-4o-mini
# Leave blank locally. Set to /proxy/8000 only when using Vocareum Swagger UI.
API_ROOT_PATH=

LANGCHAIN_TRACING_V2=true
LANGCHAIN_ENDPOINT=https://api.smith.langchain.com
LANGCHAIN_API_KEY=your_langsmith_key
LANGCHAIN_PROJECT=week16-operational-agent-api
```

Set `LANGCHAIN_TRACING_V2=false` if you do not want LangSmith tracing. The API and agent still work.

## Run locally or in Vocareum

Run commands **from this project folder**. The folder matters because Python must be able to find the `app` package.

```bash
cd "Week 16 Deploy Agentic Sys/Week_16_Live Session Activities/operational_agent_api/operational_agent_api"
```

### 1. Check and align installed libraries first

```bash
python -c "import fastapi, uvicorn, requests, langchain_core, langchain_openai; print('Required libraries are available')"
```

On Vocareum, run this compatibility installation once. It uses your user package area and fixes a possible FastAPI?Starlette version mismatch:

```bash
python -m pip install --user --upgrade --force-reinstall "fastapi==0.115.12" "starlette==0.46.2" "uvicorn>=0.27,<0.31"
```

Then install the remaining requirements only if the library-check command reports a missing module:

```bash
python -m pip install --user -r requirements.txt
```

### 2. Run the local checks

```bash
python verify.py
```

This does not call the LLM. It verifies rule routing and session-memory behaviour.

### 3. Start the API — Terminal 1

```bash
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
```

or 

PYTHONWARNINGS=ignore python -m uvicorn app.main:app --host 0.0.0.0 --port 8000

For local development, add `--reload` to restart the server whenever a Python file changes.

### 4. Call the API — Terminal 2

```bash
python demo_client.py
```

Expected checks:

- `GET /health` returns `status: ok`.
- A status question follows the rule route.
- A general question follows the LLM-agent route.

To test a different port, set `API_BASE_URL` before running the client:

```bash
# PowerShell
$env:API_BASE_URL = "http://127.0.0.1:8001"
python demo_client.py
```

### 5. Call GET and POST endpoints directly

Keep the API running in Terminal 1. These examples show that an endpoint is an HTTP contract, not only a screen in a frontend application.

#### GET endpoints ? browser or terminal

A browser address bar can call a **GET** endpoint because it does not need a request body:

```text
https://vocproxy-.../proxy/8000/
https://vocproxy-.../proxy/8000/health
https://vocproxy-.../proxy/8000/openapi.json
```

From the Vocareum terminal, the same endpoints can be called directly on the running server:

```bash
curl http://127.0.0.1:8000/
curl http://127.0.0.1:8000/health
```

#### POST endpoint ? terminal, Swagger, frontend or another agent

`POST /chat` needs a JSON body, so typing its URL in a browser address bar is not enough. Call it from the Vocareum terminal with `curl`:

```bash
curl -X POST "http://127.0.0.1:8000/chat" \
  -H "Content-Type: application/json" \
  -d '{"query":"What is the system status?"}'
```

This simple status query follows the rule route and does not need an LLM call. Then try an LLM-agent request:

```bash
curl -X POST "http://127.0.0.1:8000/chat" \
  -H "Content-Type: application/json" \
  -d '{"query":"Explain why request IDs help diagnose an agent failure."}'
```

A React frontend, Python client, workflow engine or another agent would send the same `POST /chat` request programmatically.

### 6. Use the interactive documentation

- **Local VS Code/browser:** keep `API_ROOT_PATH` blank and open `http://127.0.0.1:8000/docs`.
- **Vocareum:** add this line to `.env` before starting the API:

  ```env
  API_ROOT_PATH=/proxy/8000
  ```

  Then use the lab proxy URL, for example `https://vocproxy-.../proxy/8000/docs`. This makes Swagger request `/proxy/8000/openapi.json` rather than an incorrect root-level `/openapi.json`. If the Space or lab uses a different proxied port, replace `8000` with that port.

In Swagger UI, expand `POST /chat`, select **Try it out**, and send:

```json
{
  "query": "What is the system status?"
}
```

Try invalid JSON such as `{}` to observe Pydantic’s automatic `422` validation response.

Stop the API with `Ctrl+C` in Terminal 1 when finished.

## What to observe in the demo

- The same API can serve a frontend, a Python client, another agent or an automation workflow.
- The response includes `routing_path`, `session_id` and `latency_ms`.
- Response headers include `X-Request-ID` and `X-Process-Time` for operational diagnosis.
- Simple questions avoid an unnecessary LLM call; complex questions go to the configured model.
- LangSmith shows the agent trace when tracing is enabled.

## Optional cloud deployment

The class deployment path is a free Gradio Space or Render deployment. The local FastAPI version remains the clearest way to demonstrate API endpoints and Swagger documentation. Docker-based Hugging Face Spaces are optional and require an eligible paid Hugging Face plan.
