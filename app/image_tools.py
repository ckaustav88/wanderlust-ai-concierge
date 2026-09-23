"""Image generation tools for Wanderlust AI travel concierge using Vertex AI Gemini Image models."""

import os
import re
from google import genai
from google.genai import types
from google.cloud import storage
from google.adk.tools import ToolContext

# Hardcoded project ID and GCS bucket name as required
PROJECT_ID = "qwiklabs-gcp-02-fea4f9d45c61"
BUCKET_NAME = "wanderlust-ai-concierge-media-fea4f9d4"


async def generate_destination_image(
    prompt: str, filename: str, tool_context: ToolContext
) -> str:
    """Generate a high-quality travel image or postcard using the gemini-3.1-flash-lite-image model in the global region.

    Saves the image to the Playground's Artifacts panel via tool_context.save_artifact and uploads the bytes directly
    to the public Cloud Storage bucket, returning its public HTTPS URL.

    Args:
        prompt: Detailed description of the travel scene, destination, or postcard to generate.
        filename: Target name for the image file/artifact (e.g. 'kyoto_zen_garden.png').
        tool_context: ADK ToolContext instance injected by the framework.

    Returns:
        The public HTTPS URL (https://storage.googleapis.com/<bucket>/<object>) of the generated image.
    """
    try:
        # Normalize filename
        clean_name = re.sub(r"[^a-zA-Z0-9_\-\.]", "_", filename.strip())
        if not clean_name.lower().endswith((".png", ".jpg", ".jpeg")):
            clean_name += ".png"

        # Initialize Vertex AI GenAI Client in global region
        genai_client = genai.Client(
            vertexai=True,
            project=PROJECT_ID,
            location="global",
        )

        # Generate image using gemini-3.1-flash-lite-image
        response = genai_client.models.generate_content(
            model="gemini-3.1-flash-lite-image",
            contents=prompt,
            config=types.GenerateContentConfig(
                response_modalities=["IMAGE"],
            ),
        )

        image_bytes = None
        mime_type = "image/png" if clean_name.endswith(".png") else "image/jpeg"

        if response.candidates:
            for candidate in response.candidates:
                if candidate.content and candidate.content.parts:
                    for part in candidate.content.parts:
                        if part.inline_data and part.inline_data.data:
                            image_bytes = part.inline_data.data
                            if part.inline_data.mime_type:
                                mime_type = part.inline_data.mime_type
                            break

        if not image_bytes:
            return f"Error: Failed to extract image bytes from model response for prompt '{prompt}'."

        # Action (1): Save image with tool_context.save_artifact for Playground Artifacts panel
        artifact_part = types.Part.from_bytes(data=image_bytes, mime_type=mime_type)
        await tool_context.save_artifact(filename=clean_name, artifact=artifact_part)

        # Action (2): Upload image bytes directly to public GCS bucket (no local file writing)
        storage_client = storage.Client(project=PROJECT_ID)
        bucket = storage_client.bucket(BUCKET_NAME)
        blob = bucket.blob(clean_name)
        blob.upload_from_string(image_bytes, content_type=mime_type)

        public_url = f"https://storage.googleapis.com/{BUCKET_NAME}/{clean_name}"
        return f"Image generated successfully! Public URL: {public_url}"

    except Exception as e:
        return f"Error generating image for '{prompt}': {str(e)}"
