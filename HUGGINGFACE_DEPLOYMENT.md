# Deploy Operational Agent API on Hugging Face Spaces

This demo is an **API-only Docker Space**. The useful pages after deployment are:

* `/` — API status and endpoint links.
* `/health` — health check.
* `/docs` — Swagger UI, where learners can run `POST /chat` without a separate client.

## 1. Create the Space

1. Sign in to Hugging Face and select **New Space**.
2. Enter a name such as `week16-operational-agent-api`.
3. Select **Docker** as the SDK. Choose private or protected visibility when using a shared course key.
4. Create the Space, then upload this folder or push it as a Git repository.

The `README.md` front matter tells Hugging Face to expose Docker port `7860`; the `Dockerfile` starts Uvicorn on the same port.

## 2. Configure secrets and variables

In **Settings → Variables and secrets**, add the values shown in `.env.example`.

Use **Secrets** for `OPENAI_API_KEY`, `OPENAI_BASE_URL` and `LANGCHAIN_API_KEY`. Use **Variables** for model and LangSmith configuration. Never upload the local `.env` file.

For a first deployment, set `LANGCHAIN_TRACING_V2=false` if you do not want to configure LangSmith yet. The API continues to work without tracing.

## 3. Verify the deployed API

1. Wait for the Space status to become **Running**.
2. Open `<your-space-url>/health`; expect `{"status":"ok","version":"1.0.0"}`.
3. Open `<your-space-url>/docs`.
4. Expand `POST /chat`, select **Try it out**, and submit:

```json
{
  "query": "Tell me a short joke about programming.",
  "session_id": "hf-demo-1"
}
```

5. Submit `What is the system status?` to observe the deterministic `rule` route. Then submit the joke query to observe the LLM `agent` route.

## What this demonstrates

The Space provides a small deployment target for discussing container build, runtime configuration, secrets, API health checks, routes, structured logs and LangSmith tracing. It is a classroom deployment, not a hardened public production service: add authentication, rate limits, persistent memory, a managed secret store and a CI/CD release process before deploying a real business agent.
