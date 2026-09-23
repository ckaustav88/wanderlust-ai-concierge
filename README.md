# Wanderlust AI Concierge ✈️

Wanderlust AI Concierge is an intelligent, multi-modal travel assistant built with the Google Agent Development Kit (ADK) and deployed as an Agent-to-Agent (A2A) service on Google Cloud. It provides personalized travel itineraries, dietary-aware restaurant recommendations, live weather reports, currency conversion, custom postcard generation, and short destination video previews.

![Wanderlust AI Concierge Demo](demo.gif)

---

## 🌟 Implemented Features & Architecture

### 🧠 Core Agent Reasoning & Memory
* **Gemini 2.5 Flash**: Powered by `gemini-2.5-flash` for fast multi-step reasoning, tool routing, and structured travel concierge responses.
* **ADK Memory Bank Integration**: Integrated via `PreloadMemoryTool` and session memory callbacks to remember user preferences, dietary restrictions, and allergies across sessions.

### 🎨 Media Generation & Cloud Storage
* **AI Travel Postcard Generation**: `generate_destination_image` generates high-quality destination imagery using `gemini-3.1-flash-lite-image` in the global region.
* **AI Short Video Generation**: `generate_destination_video` generates short travel preview clips using `gemini-omni-flash-preview` via the Vertex AI Interactions API in the global region.
* **Artifact & Cloud Storage Integration**: Generated media is saved to the ADK Playground Artifacts panel via `tool_context.save_artifact` and uploaded to a public Google Cloud Storage bucket (`https://storage.googleapis.com/<bucket>/<object>`).

### 🗄️ Database & Security Sandbox
* **Google Cloud Firestore**: `search_destinations` and `add_destination` provide database lookups and persistent storage for curated travel destinations.
* **Agent Engine Code Execution Sandbox**: `AgentEngineSandboxCodeExecutor` runs Python code in a secure Vertex AI sandbox for budget calculations, currency math, and statistical travel breakdowns.

### 🗺️ Real-Time Travel APIs
* **Live Weather Reports**: `get_live_weather` fetches real-time temperature and weather conditions via the Open-Meteo API.
* **Geocoding & Nearby Attractions**: `geocode_address` and `find_nearby_places` utilize OpenStreetMap and Overpass APIs to find nearby attractions, dining, and lodging around exact coordinates.
* **Currency Conversion**: `convert_currency` calculates live exchange rates for international travel budgeting.
* **Destination Info Summaries**: `get_destination_info` retrieves historical background and travel highlights from Wikipedia.

### 💻 Frontend & A2UI Dialogue Surface
* **Minimal FastAPI Proxy**: Relays requests securely from the browser to the deployed A2A agent over the A2A protocol.
* **A2UI Rendering**: Displays rich UI cards (`Card`, `Column`, `Row`, `Text`, `Image`) directly in the chat dialogue interface without full page reloads.

---

## 📋 Capabilities Status

| Feature | Status | Technology |
|---|---|---|
| Itinerary Generation | **Implemented** | Gemini 2.5 Flash |
| Allergy & Preference Memory | **Implemented** | ADK Memory Bank |
| Real-Time Weather | **Implemented** | Open-Meteo API |
| Destination Info Search | **Implemented** | Wikipedia REST API |
| Map Geocoding & Nearby Places | **Implemented** | OpenStreetMap / Overpass |
| Curated Destination DB | **Implemented** | Google Cloud Firestore |
| Budget & Currency Math | **Implemented** | Agent Engine Code Sandbox |
| Postcard Image Generation | **Implemented** | `gemini-3.1-flash-lite-image` |
| Destination Video Generation | **Implemented** | `gemini-omni-flash-preview` |
| Flight & Hotel Booking Engine | *Planned, not yet implemented* | External API Integration |

---

## 🚀 Setup & Local Execution

### Prerequisites
* Python 3.10+
* Google Cloud SDK (`gcloud`) authenticated with target GCP project
* `uv` or `pip` package manager

### 1. Environment Setup

Set your Google Cloud project and credentials:

```bash
export GCP_PROJECT="your-gcp-project-id"
export GOOGLE_APPLICATION_CREDENTIALS="/path/to/key.json"
gcloud config set project $GCP_PROJECT
```

### 2. Install Dependencies

Install required Python dependencies:

```bash
uv pip install -r frontend/requirements.txt
```

### 3. Local Execution

Set environment variables for your agent engine resource name and application directory, then start the FastAPI server:

```bash
export AGENT_ENGINE_RESOURCE_NAME="projects/<project-number>/locations/<region>/reasoningEngines/<id>"
export AGENT_DIRECTORY="app"
export PORT=8080

cd frontend
python main.py
```

Access the chat interface in your browser at port `8080`.

### 4. Deployment Commands

To deploy the agent and frontend to Google Cloud:

```bash
# Deploy agent to Agent Runtime using agents-cli
uv run agents-cli deploy --region us-east1 --project $GCP_PROJECT --no-confirm-project

# Deploy frontend proxy to Cloud Run
gcloud run deploy wanderlust-frontend \
  --source ./frontend \
  --region us-central1 \
  --project $GCP_PROJECT \
  --set-env-vars "AGENT_ENGINE_RESOURCE_NAME=$AGENT_ENGINE_RESOURCE_NAME,AGENT_DIRECTORY=app" \
  --allow-unauthenticated
```
