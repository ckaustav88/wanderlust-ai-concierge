"""Video generation tools for Wanderlust AI travel concierge using Vertex AI Gemini Omni model."""

import os
import re
from google import genai
from google.genai import types
from google.cloud import storage
from google.adk.tools import ToolContext

# Hardcoded project ID and GCS bucket name as required
PROJECT_ID = "qwiklabs-gcp-02-fea4f9d45c61"
BUCKET_NAME = "wanderlust-ai-concierge-media-fea4f9d4"


async def generate_destination_video(
    prompt: str, filename: str, tool_context: ToolContext
) -> str:
    """Generate a short video preview for a travel destination, attraction, or scenic view using the gemini-omni-flash-preview model in the global region.

    Saves the video to the Playground's Artifacts panel via tool_context.save_artifact and uploads the bytes directly
    to the public Cloud Storage bucket, returning its public HTTPS URL.

    Args:
        prompt: Detailed description of the video scene, travel destination, or attraction to generate.
        filename: Target filename for the video file/artifact (e.g. 'kyoto_bamboo_forest.mp4').
        tool_context: ADK ToolContext instance injected by the framework.

    Returns:
        The public HTTPS URL (https://storage.googleapis.com/<bucket>/<object>) of the generated video.
    """
    try:
        # Clean up filename and ensure .mp4 extension
        clean_name = re.sub(r"[^a-zA-Z0-9_\-\.]", "_", filename.strip())
        if not clean_name.lower().endswith((".mp4", ".webm")):
            clean_name += ".mp4"

        # Initialize GenAI client with vertexai=True and location="global"
        genai_client = genai.Client(
            vertexai=True,
            project=PROJECT_ID,
            location="global",
        )

        # Generate video using gemini-omni-flash-preview via Interactions API
        interaction = genai_client.interactions.create(
            model="gemini-omni-flash-preview",
            input=prompt,
            response_modalities=["video"],
        )

        video_bytes = None
        mime_type = "video/mp4"

        if interaction and hasattr(interaction, "outputs") and interaction.outputs:
            for output in interaction.outputs:
                if getattr(output, "type", None) == "video" and getattr(output, "video", None):
                    v = output.video
                    if getattr(v, "bytes", None):
                        video_bytes = v.bytes
                    if getattr(v, "mime_type", None):
                        mime_type = v.mime_type
                    break

        if not video_bytes:
            return f"Error: Failed to extract video bytes from model response for prompt '{prompt}'."

        # Action (1): Save video with tool_context.save_artifact for Playground Artifacts panel
        artifact_part = types.Part.from_bytes(data=video_bytes, mime_type=mime_type)
        await tool_context.save_artifact(filename=clean_name, artifact=artifact_part)

        # Action (2): Upload video bytes directly to public GCS bucket (no local file writing)
        storage_client = storage.Client(project=PROJECT_ID)
        bucket = storage_client.bucket(BUCKET_NAME)
        blob = bucket.blob(clean_name)
        blob.upload_from_string(video_bytes, content_type=mime_type)

        public_url = f"https://storage.googleapis.com/{BUCKET_NAME}/{clean_name}"
        return f"Video generated successfully! Public URL: {public_url}"

    except Exception as e:
        return f"Error generating video for '{prompt}': {str(e)}"
