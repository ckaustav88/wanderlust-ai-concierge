"""Google Maps API tools (Geocoding API and Places API (New)) for Wanderlust AI travel concierge."""

import json
import os
import urllib.parse
import urllib.request
from dotenv import load_dotenv

# Load environment variables from .env file if present
load_dotenv()


def geocode_address(address: str) -> str:
    """Turn a street address or location name into geographic coordinates (latitude and longitude).

    Args:
        address: The address or place name to geocode (e.g. 'Kyoto Station, Japan' or 'Eiffel Tower, Paris').

    Returns:
        Formatted summary with key fields: formatted address, latitude, and longitude.
    """
    api_key = os.getenv("GOOGLE_MAPS_API_KEY", "").strip()
    if not api_key:
        return "Error: GOOGLE_MAPS_API_KEY environment variable is not configured."

    encoded_address = urllib.parse.quote(address.strip())
    url = f"https://maps.googleapis.com/maps/api/geocode/json?address={encoded_address}&key={api_key}"

    try:
        req = urllib.request.Request(url, headers={"User-Agent": "WanderlustAI/1.0"})
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode("utf-8"))

        status = data.get("status")
        if status != "OK" or not data.get("results"):
            return f"Geocoding failed for '{address}'. Status: {status}"

        result = data["results"][0]
        formatted_address = result.get("formatted_address", address)
        loc = result.get("geometry", {}).get("location", {})
        lat = loc.get("lat")
        lng = loc.get("lng")

        return (
            f"Geocoding Result for '{address}':\n"
            f"- Address: {formatted_address}\n"
            f"- Location Coordinates: Latitude {lat}, Longitude {lng}"
        )
    except Exception as e:
        return f"Error executing Geocoding request for '{address}': {str(e)}"


def find_nearby_places(
    latitude: float,
    longitude: float,
    place_type: str = "restaurant",
    radius_meters: float = 1000.0,
) -> str:
    """Search for nearby places (restaurants, attractions, hotels, cafes, etc.) around given coordinates using Google Places API (New).

    Args:
        latitude: Target center latitude (e.g. 34.985849).
        longitude: Target center longitude (e.g. 135.7587667).
        place_type: Type of place to search for (e.g. 'restaurant', 'tourist_attraction', 'lodging', 'cafe', 'museum').
        radius_meters: Search radius in meters (default: 1000.0).

    Returns:
        Formatted list of nearby places with key fields: name, address, and location coordinates.
    """
    api_key = os.getenv("GOOGLE_MAPS_API_KEY", "").strip()
    if not api_key:
        return "Error: GOOGLE_MAPS_API_KEY environment variable is not configured."

    url = "https://places.googleapis.com/v1/places:searchNearby"
    headers = {
        "Content-Type": "application/json",
        "X-Goog-Api-Key": api_key,
        "X-Goog-FieldMask": "places.displayName,places.formattedAddress,places.location",
        "User-Agent": "WanderlustAI/1.0",
    }

    body = {
        "includedTypes": [place_type.lower().strip()],
        "maxResultCount": 5,
        "locationRestriction": {
            "circle": {
                "center": {
                    "latitude": float(latitude),
                    "longitude": float(longitude),
                },
                "radius": float(radius_meters),
            }
        },
    }

    try:
        req = urllib.request.Request(
            url,
            data=json.dumps(body).encode("utf-8"),
            headers=headers,
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode("utf-8"))

        places = data.get("places", [])
        if not places:
            return f"No nearby '{place_type}' places found within {radius_meters}m of ({latitude}, {longitude})."

        output = [f"Found {len(places)} nearby '{place_type}' places within {radius_meters}m:"]
        for p in places:
            name = p.get("displayName", {}).get("text", "Unknown Name")
            addr = p.get("formattedAddress", "N/A")
            loc = p.get("location", {})
            p_lat = loc.get("latitude")
            p_lng = loc.get("longitude")
            output.append(
                f"- Name: {name}\n"
                f"  Address: {addr}\n"
                f"  Location: ({p_lat}, {p_lng})"
            )

        return "\n".join(output)
    except Exception as e:
        return f"Error querying Places API (New): {str(e)}"
