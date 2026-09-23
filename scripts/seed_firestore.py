#!/usr/bin/env python3
"""Seed Firestore with sample travel destinations for Wanderlust AI."""

from google.cloud import firestore

PROJECT_ID = "qwiklabs-gcp-02-fea4f9d45c61"
COLLECTION_NAME = "destinations"


def seed_database():
    db = firestore.Client(project=PROJECT_ID)

    sample_destinations = [
        {
            "id": "kyoto-cultural",
            "name": "Kyoto Temple & Cultural Exploration",
            "city": "Kyoto",
            "category": "Cultural",
            "description": "Historic Gion walk, Nanzen-ji temple, traditional ryokan lodging, and kaiseki dining.",
            "est_cost_usd": 350,
            "tags": ["temples", "culture", "ryokan", "peanut-free-friendly"],
        },
        {
            "id": "tokyo-luxury",
            "name": "Tokyo High-End Culinary & Shopping Tour",
            "city": "Tokyo",
            "category": "Luxury",
            "description": "Boutique luxury hotel in Ginza, omakase sushi experience, and private art museum tours.",
            "est_cost_usd": 600,
            "tags": ["luxury", "shopping", "sushi", "boutique-hotel"],
        },
        {
            "id": "hakone-onsen",
            "name": "Hakone Onsen & Mountain Retreat",
            "city": "Hakone",
            "category": "Wellness",
            "description": "Private thermal bath spring, Mount Fuji views, open-air art museum, and hot pot dining.",
            "est_cost_usd": 400,
            "tags": ["onsen", "wellness", "nature", "relaxation"],
        },
    ]

    for item in sample_destinations:
        doc_ref = db.collection(COLLECTION_NAME).document(item["id"])
        doc_ref.set(item)
        print(f"Seeded document: {item['id']} in collection '{COLLECTION_NAME}'")

    print(f"Successfully seeded {len(sample_destinations)} items into Firestore!")


if __name__ == "__main__":
    seed_database()
