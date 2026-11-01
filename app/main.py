"""
FastAPI entry point for the operational-agent demo.

FastAPI exposes the agent through HTTP endpoints so a frontend, another agent,
or an automation workflow can call it using the same documented contract.
"""
import os
import time
import uuid
from typing import Optional

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel

# Load configuration before the agent imports create the LLM client.
load_dotenv(override=True)

from .core.agent import get_agent_response
from .core.memory import memory_store
from .core.router import route_request
from .observability.langsmith import configure_tracing
from .observability.logging import logger

# A reverse proxy (such as Vocareum) may expose this server below a path such
# as /proxy/8000. Set API_ROOT_PATH=/proxy/8000 in that environment so Swagger
# requests /proxy/8000/openapi.json rather than the incorrect root /openapi.json.
api_root_path = os.getenv("API_ROOT_PATH", "").rstrip("/")

# FastAPI creates an ASGI application. ASGI supports concurrent, I/O-heavy web
# workloads such as requests that wait for an LLM, database or external tool.
app = FastAPI(
    title="Operational Agent API",
    version="1.0.0",
    root_path=api_root_path,
)


# Pydantic models define and validate the API contract. FastAPI uses them to:
# - validate incoming JSON automatically;
# - return a 422 response for invalid requests; and
# - generate the interactive /docs API documentation.
class AgentRequest(BaseModel):
    query: str
    session_id: Optional[str] = None


class AgentResponse(BaseModel):
    response: str
    session_id: str
    routing_path: str
    latency_ms: float


@app.on_event("startup")
async def startup_event():
    """FastAPI lifecycle hook: configure tracing once when the API starts."""
    configure_tracing()
    logger.info("system_startup", message="Operational Agent API started")


@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    """Add request-level observability around every endpoint call.

    Middleware runs before and after the endpoint. The `await call_next(...)`
    pattern lets the server handle other I/O-ready requests while it waits.
    """
    request_id = str(uuid.uuid4())
    start_time = time.time()

    logger.info(
        "request_received",
        request_id=request_id,
        path=request.url.path,
        method=request.method,
    )

    response = await call_next(request)
    process_time = (time.time() - start_time) * 1000

    logger.info(
        "request_completed",
        request_id=request_id,
        status_code=response.status_code,
        latency_ms=round(process_time, 2),
    )

    # Headers let a frontend, API gateway or support team correlate a visible
    # response with its log entries.
    response.headers["X-Request-ID"] = request_id
    response.headers["X-Process-Time"] = str(process_time)
    return response


@app.get("/health")
async def health_check():
    """Lightweight endpoint used by users, load balancers and deployment checks."""
    return {"status": "ok", "version": "1.0.0"}


@app.get("/")
async def api_home():
    """Small landing response useful when the API is hosted on a cloud platform."""
    return {
        "service": "Operational Agent API",
        "status": "running",
        "health": "/health",
        "interactive_docs": "/docs",
        "chat_endpoint": "POST /chat",
    }


@app.post("/chat", response_model=AgentResponse)
async def chat_endpoint(request: AgentRequest):
    """Serve one agent interaction through a documented, validated endpoint.

    Any HTTP client can call this endpoint: a React frontend, another agent,
    an automation workflow or the supplied `demo_client.py` script.
    """
    request_start = time.time()
    session_id = request.session_id or str(uuid.uuid4())

    try:
        # First make a cheap deterministic routing decision. In a production
        # system this could itself be traced as a separate observability span.
        route = route_request(request.query)

        if route == "rule":
            # Avoid an LLM call for simple operational questions.
            if "status" in request.query.lower():
                response_text = "System is operational. All subsystems go."
            elif "version" in request.query.lower():
                response_text = "Operational Agent API v1.0.0"
            else:
                response_text = "Acknowledged. Rule-based path executed."

            # Keep both paths consistent for the memory demonstration.
            memory_store.add_message(session_id, "user", request.query)
            memory_store.add_message(session_id, "assistant", response_text)
        else:
            # The agent path can make an LLM call and use the supplied session.
            response_text = get_agent_response(session_id, request.query)

        latency = (time.time() - request_start) * 1000
        logger.info(
            "agent_interaction",
            session_id=session_id,
            query=request.query,
            route=route,
            latency_ms=round(latency, 2),
            outcome="success",
        )

        return AgentResponse(
            response=response_text,
            session_id=session_id,
            routing_path=route,
            latency_ms=round(latency, 2),
        )

    except Exception as exc:
        # Convert an internal Python error into an explicit HTTP 500 response.
        # Do not send raw exception details to the API client.
        logger.error(
            "agent_failure",
            session_id=session_id,
            error=str(exc),
            query=request.query,
        )
        raise HTTPException(status_code=500, detail="Internal Agent Error") from exc
