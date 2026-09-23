"""Real-time travel data tools integrating free public APIs (Open-Meteo and Wikipedia)."""

import json
import os
import urllib.parse
import urllib.request


def get_live_weather(city: str) -> str:
    """Fetch real-time current weather and geographical details for any city worldwide using the free Open-Meteo API.

    Args:
        city: The name of the target city or destination (e.g. 'Kyoto', 'Tokyo', 'Paris').

    Returns:
        Real-time weather conditions including temperature, wind speed, timezone, and country.
    """
    try:
        encoded_city = urllib.parse.quote(city.strip())
        geo_url = f"https://geocoding-api.open-meteo.com/v1/search?name={encoded_city}&count=1&language=en&format=json"

        # Check for optional API key in environment variable if specified by host configuration
        api_key = os.getenv("OPEN_METEO_API_KEY", "")
        if api_key:
            geo_url += f"&apikey={urllib.parse.quote(api_key)}"

        req = urllib.request.Request(geo_url, headers={"User-Agent": "WanderlustAI/1.0"})
        with urllib.request.urlopen(req, timeout=5) as resp:
            geo_data = json.loads(resp.read().decode("utf-8"))

        results = geo_data.get("results")
        if not results:
            return f"Could not find coordinates for city '{city}' via Open-Meteo API."

        loc = results[0]
        lat, lon = loc["latitude"], loc["longitude"]
        city_name = loc.get("name", city)
        country = loc.get("country", "")
        timezone = loc.get("timezone", "UTC")

        # Fetch live weather forecast
        weather_url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current_weather=true"
        if api_key:
            weather_url += f"&apikey={urllib.parse.quote(api_key)}"

        w_req = urllib.request.Request(weather_url, headers={"User-Agent": "WanderlustAI/1.0"})
        with urllib.request.urlopen(w_req, timeout=5) as w_resp:
            w_data = json.loads(w_resp.read().decode("utf-8"))

        current = w_data.get("current_weather", {})
        temp_c = current.get("temperature")
        wind_speed = current.get("windspeed")
        time_str = current.get("time")

        if temp_c is None:
            return f"Weather data unavailable for {city_name}."

        temp_f = round((temp_c * 9 / 5) + 32, 1)

        return (
            f"Live Weather for {city_name}, {country} ({timezone}):\n"
            f"- Temperature: {temp_c}°C / {temp_f}°F\n"
            f"- Wind Speed: {wind_speed} km/h\n"
            f"- Coordinates: Lat {lat}, Lon {lon}\n"
            f"- Recorded at: {time_str}"
        )
    except Exception as e:
        return f"Error fetching live weather for '{city}': {str(e)}"


def get_destination_info(destination: str) -> str:
    """Fetch real-time encyclopedic summary and background for any travel destination or landmark via Wikipedia REST API.

    Args:
        destination: Name of the landmark, city, or attraction (e.g. 'Fushimi Inari-taisha', 'Kyoto', 'Eiffel Tower').

    Returns:
        A concise, real-time background summary of the destination.
    """
    try:
        formatted_dest = urllib.parse.quote(destination.strip().replace(" ", "_"))
        wiki_url = f"https://en.wikipedia.org/api/rest_v1/page/summary/{formatted_dest}"

        req = urllib.request.Request(wiki_url, headers={"User-Agent": "WanderlustAI/1.0"})
        with urllib.request.urlopen(req, timeout=5) as resp:
            data = json.loads(resp.read().decode("utf-8"))

        title = data.get("title", destination)
        extract = data.get("extract", "")
        description = data.get("description", "")
        page_url = data.get("content_urls", {}).get("desktop", {}).get("page", "")

        if not extract:
            return f"No detailed summary found for destination '{destination}'."

        return (
            f"Destination Guide for '{title}' ({description}):\n"
            f"{extract}\n"
            f"Learn more: {page_url}"
        )
    except Exception as e:
        return f"Error fetching destination guide for '{destination}': {str(e)}"
