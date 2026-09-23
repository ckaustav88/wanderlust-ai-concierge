"""Minimal FastAPI proxy for a deployed A2A agent (Agent Runtime, agents-cli 1.1.0+).

The browser talks ONLY to this proxy (same origin, no CORS, no GCP creds in the
browser). The proxy authenticates with Application Default Credentials and
forwards chat to the deployed agent over the A2A protocol, returning replies as
structured parts the chat UI knows how to show:

  * {"kind": "text", "text": ...}  -> a normal chat bubble
  * {"kind": "a2ui", "data": ...}  -> one A2UI message (beginRendering /
    surfaceUpdate); static/index.html renders these as a card.

Why A2A: agents-cli 1.1.0 (GA) deploys ADK agents to Agent Runtime as A2A agents
and no longer registers the reasoning-engine operation schema the old
`agent_engines.get(...).stream_query()` path relied on (operation_schemas() comes
back empty). The container serves the A2A protocol over the Agent Engine HTTP
passthrough, so this proxy fetches the agent's card and sends messages with the
a2a-sdk client (the same path `agents-cli run --mode a2a` uses). This works for
both A2A and plain ADK 1.1.0 deployments (the container serves A2A either way).

Run:
  pip install -r requirements.txt
  export AGENT_ENGINE_RESOURCE_NAME="projects/.../locations/.../reasoningEngines/..."
  export AGENT_DIRECTORY="app"   # your agent's app directory (agents-cli-manifest.yaml)
  python main.py                 # -> http://localhost:8080
"""

import os
import uuid

import google.auth
import google.auth.transport.requests
import httpx
from a2a.client import ClientConfig, ClientFactory
import a2a.types as _a2a_types

AgentCard = getattr(_a2a_types, "AgentCard", None)
Message = getattr(_a2a_types, "Message", None)
Part = getattr(_a2a_types, "Part", None)
Role = getattr(_a2a_types, "Role", None)
SendMessageConfiguration = getattr(
    _a2a_types,
    "SendMessageConfiguration",
    getattr(_a2a_types, "MessageSendConfiguration", None),
)
SendMessageRequest = getattr(_a2a_types, "SendMessageRequest", None)
TaskArtifactUpdateEvent = getattr(_a2a_types, "TaskArtifactUpdateEvent", None)
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

RESOURCE = os.environ["AGENT_ENGINE_RESOURCE_NAME"]
# The agent's app directory (matches agent_directory in agents-cli-manifest.yaml).
AGENT_DIRECTORY = os.environ.get("AGENT_DIRECTORY", "app")
# Location is embedded in the resource name: projects/<p>/locations/<loc>/reasoningEngines/<id>.
LOCATION = RESOURCE.split("/locations/")[1].split("/")[0]

# A2A endpoint for an Agent Runtime deployment, via the Agent Engine HTTP
# passthrough. The card lives at the well-known path under this base.
A2A_BASE = (
    f"https://{LOCATION}-aiplatform.googleapis.com/reasoningEngines/v1/"
    f"{RESOURCE}/api/a2a/{AGENT_DIRECTORY}"
)
A2A_CARD_URL = f"{A2A_BASE}/.well-known/agent-card.json"

# The agent tags its A2UI data parts with this mime type.
_A2UI_MIME = "application/json+a2ui"

# One set of ADC credentials, refreshed per request (access tokens expire ~1h).
_creds, _ = google.auth.default(
    scopes=["https://www.googleapis.com/auth/cloud-platform"]
)


def _auth_headers() -> dict[str, str]:
    _creds.refresh(google.auth.transport.requests.Request())
    return {
        "Authorization": f"Bearer {_creds.token}",
        "Content-Type": "application/json",
    }


app = FastAPI()


@app.exception_handler(Exception)
async def _json_errors(request: Request, exc: Exception):
    # Always return JSON so the browser never receives a plain-text 500 page
    # (which shows up in the chat as "Unexpected token 'I', "Internal S"... is
    # not valid JSON"). Any server-side failure now surfaces as a readable
    # message in the chat bubble instead.
    return JSONResponse(
        status_code=200,
        content={
            "parts": [{"kind": "text", "text": f"Error: {type(exc).__name__}: {exc}"}]
        },
    )


# Reuse ONE A2A context per user so the agent remembers the conversation.
_contexts: dict[str, str] = {}
# Cache the agent card after the first fetch.
_card: AgentCard | None = None


from google.protobuf.json_format import ParseDict


async def _get_card(client: httpx.AsyncClient) -> AgentCard:
    global _card
    if _card is None:
        resp = await client.get(A2A_CARD_URL)
        resp.raise_for_status()
        card_data = resp.json()

        try:
            card = AgentCard()
            ParseDict(card_data, card, ignore_unknown_fields=True)
            for interface in getattr(card, "supported_interfaces", []):
                interface.url = A2A_BASE
        except Exception:
            if isinstance(card_data, dict):
                for key in ("supportedInterfaces", "supported_interfaces"):
                    if key in card_data:
                        for iface in card_data[key]:
                            if isinstance(iface, dict):
                                iface["url"] = A2A_BASE
            if hasattr(AgentCard, "model_validate"):
                card = AgentCard.model_validate(card_data)
            elif hasattr(AgentCard, "parse_obj"):
                card = AgentCard.parse_obj(card_data)
            else:
                card = AgentCard(**card_data)

        _card = card
    return _card


def _extract_parts(parts: list) -> list[dict]:
    """Turn A2A response parts into structured parts for the chat UI.

    Text parts pass through as {"kind": "text"}. A2UI data parts (tagged
    application/json+a2ui) become {"kind": "a2ui", "data": <message>} so the UI
    renders the card; each data part is one A2UI message (beginRendering or
    surfaceUpdate).
    """
    out: list[dict] = []
    for p in parts:
        root = getattr(p, "root", p)
        text = getattr(root, "text", None)
        if text:
            out.append({"kind": "text", "text": text})
            continue

        data = getattr(root, "data", None)
        if data is not None:
            data_dict = data
            if hasattr(data, "to_dict"):
                data_dict = data.to_dict()
            elif hasattr(data, "DESCRIPTOR") or type(data).__name__ in ("Struct", "Value"):
                from google.protobuf.json_format import MessageToDict

                data_dict = MessageToDict(data)

            if isinstance(data_dict, dict):
                inner_meta = data_dict.get("metadata")
                mime = inner_meta.get("mimeType") if isinstance(inner_meta, dict) else None
                if not mime:
                    meta = getattr(root, "metadata", None) or {}
                    if isinstance(meta, dict):
                        mime = meta.get("mimeType")

                if mime == _A2UI_MIME or "beginRendering" in data_dict or "surfaceUpdate" in data_dict:
                    out.append({"kind": "a2ui", "data": data_dict})
                    continue

        file_obj = getattr(root, "file", None)
        uri = getattr(file_obj, "uri", None) if file_obj else None
        if uri:
            out.append({"kind": "text", "text": uri})
    return out


@app.post("/chat")
async def chat(req: Request):
    body = await req.json()
    message = body.get("message", "")
    user_id = body.get("user_id") or "web-user"
    parts: list[dict] = []

    async with httpx.AsyncClient(headers=_auth_headers(), timeout=120) as client:
        card = await _get_card(client)
        factory = ClientFactory(ClientConfig(httpx_client=client))
        a2a_client = factory.create(card)

        user_role = getattr(Role, "user", None) or getattr(Role, "ROLE_USER", None)
        msg = Message(
            message_id=str(uuid.uuid4()),
            role=user_role,
            parts=[Part(text=message)],
            context_id=_contexts.get(user_id),
        )
        config_arg = SendMessageConfiguration() if SendMessageConfiguration else None
        if config_arg is not None:
            send_req = SendMessageRequest(message=msg, configuration=config_arg)
        else:
            send_req = SendMessageRequest(message=msg)

        last_context_id = None
        got_artifact_update = False
        async for event in a2a_client.send_message(send_req):
            # Extract context_id from task or status_update/artifact_update if present
            for field in ("task", "status_update", "artifact_update"):
                sub = getattr(event, field, None)
                if sub and getattr(sub, "context_id", None):
                    _contexts[user_id] = sub.context_id
                    break

            # Extract artifact parts from StreamResponse or tuple
            if hasattr(event, "artifact_update") and getattr(event, "artifact_update", None) and hasattr(event.artifact_update, "artifact"):
                got_artifact_update = True
                parts.extend(_extract_parts(event.artifact_update.artifact.parts))
            elif hasattr(event, "artifact"):
                got_artifact_update = True
                parts.extend(_extract_parts(event.artifact.parts))
            elif hasattr(event, "parts"):
                parts.extend(_extract_parts(event.parts))

    if not parts:
        # The turn produced no text or UI (e.g. the agent only ran tools, or a
        # tool stalled). Be honest rather than silent.
        parts = [{"kind": "text", "text": "(The agent didn't return a reply.)"}]
    return JSONResponse({"parts": parts})


# Serve the chat UI (keep this mount last so /chat wins).
static_dir = os.path.join(os.path.dirname(__file__), "static")
app.mount("/", StaticFiles(directory=static_dir, html=True), name="static")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))
