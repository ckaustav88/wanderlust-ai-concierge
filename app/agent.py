# ruff: noqa
# Copyright 2026 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import datetime
from zoneinfo import ZoneInfo

from google.adk.agents import Agent
from google.adk.agents.callback_context import CallbackContext
from google.adk.apps import App
from google.adk.models import Gemini
from google.adk.tools.preload_memory_tool import PreloadMemoryTool
from google.genai import types


MODEL = "gemini-2.5-flash"


async def generate_memories_callback(callback_context: CallbackContext):
    try:
        await callback_context.add_session_to_memory()
    except ValueError:
        pass
    return None


def get_weather(query: str) -> str:
    """Simulates a web search. Use it get information on weather.

    Args:
        query: A string containing the location to get weather information for.

    Returns:
        A string with the simulated weather information for the queried location.
    """
    if "sf" in query.lower() or "san francisco" in query.lower():
        return "It's 60 degrees and foggy."
    return "It's 90 degrees and sunny."


def get_current_time(query: str) -> str:
    """Simulates getting the current time for a city.

    Args:
        city: The name of the city to get the current time for.

    Returns:
        A string with the current time information.
    """
    if "sf" in query.lower() or "san francisco" in query.lower():
        tz_identifier = "America/Los_Angeles"
    else:
        return f"Sorry, I don't have timezone information for query: {query}."

    tz = ZoneInfo(tz_identifier)
    now = datetime.datetime.now(tz)
    return f"The current time for query {query} is {now.strftime('%Y-%m-%d %H:%M:%S %Z%z')}"


from a2ui.basic_catalog.provider import BasicCatalog
from a2ui.schema.manager import A2uiSchemaManager
from google.adk.code_executors import AgentEngineSandboxCodeExecutor
from app.a2ui_utils import a2ui_callback
from app.currency_tools import convert_currency
from app.firestore_tools import add_destination, search_destinations
from app.image_tools import generate_destination_image
from app.video_tools import generate_destination_video
from app.maps_tools import find_nearby_places, geocode_address
from app.travel_api_tools import get_destination_info, get_live_weather

SANDBOX_RESOURCE_NAME = "projects/384600850295/locations/us-central1/reasoningEngines/8532504350902190080/sandboxEnvironments/8571714035060310016"

schema_manager = A2uiSchemaManager(
    version="0.8",
    catalogs=[BasicCatalog.get_config("0.8")],
)

instruction = schema_manager.generate_system_prompt(
    role_description=(
        "You are Wanderlust AI, a personalized travel concierge assistant. "
        "CRITICAL MEMORY & PREFERENCE DIRECTIVES:\n"
        "- Actively identify, confirm, and remember all stated user allergies (e.g., peanut, gluten, dairy, shellfish), health conditions, dietary restrictions, accommodation preferences (e.g., boutique luxury, ryokans), and travel style across all sessions.\n"
        "- Always check preloaded memory at the start of every interaction and strictly incorporate all remembered user allergies and preferences into your itinerary, dining, and hotel recommendations.\n"
        "- Never suggest dining options or ingredients that conflict with remembered allergies.\n"
        "- You have built-in Python code execution in a secure Agent Engine sandbox via `code_executor` to compute travel math, budget allocations, statistical analyses, or complex itinerary schedules.\n"
        "- Use `generate_destination_image` to generate travel postcards and destination imagery using gemini-3.1-flash-lite-image.\n"
        "- Use `generate_destination_video` to generate short video previews for travel destinations using gemini-omni-flash-preview.\n"
        "- Use `geocode_address` to convert address strings or landmarks into exact latitude and longitude coordinates.\n"
        "- Use `find_nearby_places` to search for nearby restaurants, attractions, lodging, or cafes around coordinates.\n"
        "- Use `get_live_weather` to fetch real live weather conditions and coordinates for any city worldwide.\n"
        "- Use `get_destination_info` to fetch real background summaries for attractions, landmarks, or cities.\n"
        "- You have access to a Firestore database containing curated travel destinations via `search_destinations` and `add_destination`.\n"
        "- You have access to currency conversion via `convert_currency` for budget calculations."
    ),
    workflow_description="Analyze the request and return structured UI when appropriate.",
    ui_description=(
        "Keep every surface tiny and flat: ONE Card > ONE Column > a few Text rows. "
        "Never nest a Card inside a Card. "
        "Use ONLY these components: Card, Column, Row, Text, and Image. Do not use "
        "Table or Heading (unsupported), or Buttons, actions, or forms (they do "
        "nothing in adk web). "
        "You may include one Image component, but only when you have a public https "
        "URL for the image (for example the URL an image tool returns after uploading "
        "to a public bucket). Set the Image url to that exact https link, for example "
        "{\"Image\": {\"url\": {\"literalString\": \"https://...\"}}}. Never point an "
        "Image at a bare filename, an artifact name, or a non-http(s) path. If you do "
        "not have a public URL, add a short Text line noting the image instead. "
        "No markdown in text; use the usageHint property ('h1', 'h2', 'body') for "
        "headings and emphasis. "
        "Output ONLY the raw A2UI JSON array — no prose, and never wrap it in "
        "<a2a_datapart_json> tags or 'kind'/'data'/'metadata' objects."
    ),
    include_schema=True,
    include_examples=True,
)


root_agent = Agent(
    # Keep in sync with agents-cli-manifest.yaml: agents-cli derives this name
    # from the project `name:` recorded there, and telemetry reports it as
    # gen_ai.agent.name. Renaming the agent only here makes the two disagree,
    # and anything selecting traces by name stops finding this agent's.
    name="simple_agent",
    model=Gemini(
        model=MODEL,
        retry_options=types.HttpRetryOptions(attempts=3),
    ),
    code_executor=AgentEngineSandboxCodeExecutor(
        sandbox_resource_name=SANDBOX_RESOURCE_NAME
    ),
    instruction=instruction,
    tools=[
        get_weather,
        get_current_time,
        PreloadMemoryTool(),
        search_destinations,
        add_destination,
        convert_currency,
        get_live_weather,
        get_destination_info,
        geocode_address,
        find_nearby_places,
        generate_destination_image,
        generate_destination_video,
    ],
    after_model_callback=a2ui_callback,
    after_agent_callback=generate_memories_callback,
)

app = App(
    root_agent=root_agent,
    name="app",
)
