"""Firestore database integration tools for Wanderlust AI travel concierge."""

from google.cloud import firestore

# Hardcoded Project ID string as required for Agent Platform deployment
PROJECT_ID = "qwiklabs-gcp-02-fea4f9d45c61"
COLLECTION_NAME = "destinations"


def search_destinations(city: str = "", category: str = "") -> str:
    """Search for destinations or itineraries stored in the Firestore database.

    Args:
        city: Optional city filter (e.g., 'Kyoto', 'Tokyo', 'Hakone').
        category: Optional category filter (e.g., 'Cultural', 'Luxury', 'Wellness').

    Returns:
        A formatted string listing the matching travel destinations.
    """
    db = firestore.Client(project=PROJECT_ID)
    query = db.collection(COLLECTION_NAME)

    if city:
        query = query.where("city", "==", city)
    if category:
        query = query.where("category", "==", category)

    docs = list(query.stream())
    if not docs:
        return f"No destinations found matching city='{city}', category='{category}'."

    output = ["Found the following destinations in Firestore:"]
    for doc in docs:
        data = doc.to_dict()
        doc_id = doc.id
        tags_str = ", ".join(data.get("tags", []))
        output.append(
            f"- [{doc_id}] {data.get('name')} ({data.get('city')}, {data.get('category')}): "
            f"{data.get('description')} | Est. Cost: ${data.get('est_cost_usd')} | Tags: {tags_str}"
        )
    return "\n".join(output)


def add_destination(
    doc_id: str,
    name: str,
    city: str,
    category: str,
    description: str,
    est_cost_usd: int,
    tags: str = "",
) -> str:
    """Save or update a travel destination or itinerary in the Firestore database.

    Args:
        doc_id: Unique document ID slug (e.g., 'osaka-foodie-tour').
        name: Display title of the destination or itinerary experience.
        city: Target city (e.g., 'Osaka', 'Sapporo').
        category: Experience category (e.g., 'Culinary', 'Adventure', 'Cultural').
        description: Detailed summary of the destination or itinerary.
        est_cost_usd: Estimated cost in USD per person.
        tags: Comma-separated tags (e.g., 'street-food, nightlife, peanut-free').

    Returns:
        A confirmation message indicating successful persistence in Firestore.
    """
    db = firestore.Client(project=PROJECT_ID)
    tag_list = [t.strip() for t in tags.split(",") if t.strip()] if tags else []

    doc_data = {
        "name": name,
        "city": city,
        "category": category,
        "description": description,
        "est_cost_usd": est_cost_usd,
        "tags": tag_list,
    }

    db.collection(COLLECTION_NAME).document(doc_id).set(doc_data)
    return f"Successfully saved destination '{doc_id}' to Firestore collection '{COLLECTION_NAME}'!"
