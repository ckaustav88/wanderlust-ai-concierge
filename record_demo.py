import asyncio
import os
import shutil
from playwright.async_api import async_playwright

FRONTEND_URL = "https://wanderlust-frontend-2md7iv6vpa-uc.a.run.app"
RECORDINGS_DIR = "/config/.gemini/antigravity/scratch/wanderlust-ai-concierge/recordings"
ARTIFACTS_DIR = "/config/.gemini/antigravity/brain/625ab399-dc48-4659-a45a-9c59bdfdf15f"

async def record_demo():
    os.makedirs(RECORDINGS_DIR, exist_ok=True)
    os.makedirs(ARTIFACTS_DIR, exist_ok=True)

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            viewport={"width": 1280, "height": 800},
            record_video_dir=RECORDINGS_DIR,
            record_video_size={"width": 1280, "height": 800}
        )
        page = await context.new_page()

        print(f"Navigating to {FRONTEND_URL}...")
        await page.goto(FRONTEND_URL, wait_until="networkidle")
        await asyncio.sleep(2)

        # Prompt 1: Core app capability (Itinerary Planning)
        print("Submitting Prompt 1 (3-Day Kyoto Itinerary)...")
        await page.click(".chip:has-text('3-Day Kyoto')")
        await asyncio.sleep(12)

        # Prompt 2: Richer prompt with tool calls (Video Generation & Attraction Lookup)
        print("Submitting Prompt 2 (Video Generation & Attraction Lookup)...")
        input_elem = page.locator("#input")
        await input_elem.fill("Generate a short video preview of cherry blossoms in Kyoto using gemini-omni-flash-preview, and search for top rated dining destinations.")
        await page.click("button[type='submit']")

        await asyncio.sleep(20)

        await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        await asyncio.sleep(4)

        # Store video reference object
        video_obj = page.video
        await page.close()
        await context.close()
        await browser.close()

        video_path = await video_obj.path()
        print(f"Recorded video saved to: {video_path}")
        
        target_path = os.path.join(ARTIFACTS_DIR, "wanderlust_demo.webm")
        shutil.copy(video_path, target_path)
        print(f"Copied demo video to artifact path: {target_path}")

if __name__ == "__main__":
    asyncio.run(record_demo())
