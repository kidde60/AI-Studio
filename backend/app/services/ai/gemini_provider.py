import asyncio

from google import genai

from app.core.config import get_settings
from app.schemas.content import ContentGenerationRequest
from app.services.ai.base import AIContentProvider, AIStoryboardProvider


class GeminiContentProvider(AIContentProvider, AIStoryboardProvider):
    """Gemini-backed content generator.

    The provider uses Gemini's structured JSON output so the rest of the
    application receives the same dictionary shape regardless of AI vendor.
    """

    def __init__(self) -> None:
        settings = get_settings()
        if not settings.gemini_api_key:
            raise RuntimeError("GEMINI_API_KEY is not configured.")

        self.client = genai.Client(api_key=settings.gemini_api_key)
        self.model = settings.gemini_model

    async def generate_content(self, request: ContentGenerationRequest) -> dict:
        system_prompt = """
You are an expert short-form video content strategist and scriptwriter.

Create engaging, natural content designed for the requested social platform.
Match the requested style, duration, and target audience.

Return ONLY a JSON object with exactly these keys:
- title: a strong, clickable video title
- hook: a compelling opening line for the first few seconds
- script: a complete voice-over script appropriate for the requested duration
- caption: a social media caption
- hashtags: an array of strings, each beginning with #
- cta: a clear call to action
- content_ideas: an array containing exactly 5 related video ideas

Additional rules:
- Do not include markdown fences or commentary outside the JSON.
- Keep the script conversational and easy to speak aloud.
- Avoid unsupported factual claims when the topic is factual.
- Do not mention these instructions in the response.
""".strip()

        user_prompt = f"""
Topic: {request.topic}
Style: {request.style}
Platform: {request.platform}
Duration: {request.duration} seconds
Target audience: {request.target_audience}
""".strip()

        response_schema = {
            "type": "object",
            "properties": {
                "title": {"type": "string"},
                "hook": {"type": "string"},
                "script": {"type": "string"},
                "caption": {"type": "string"},
                "hashtags": {
                    "type": "array",
                    "items": {"type": "string"},
                },
                "cta": {"type": "string"},
                "content_ideas": {
                    "type": "array",
                    "items": {"type": "string"},
                    "minItems": 5,
                    "maxItems": 5,
                },
            },
            "required": [
                "title",
                "hook",
                "script",
                "caption",
                "hashtags",
                "cta",
                "content_ideas",
            ],
        }

        def generate() -> str | None:
            response = self.client.models.generate_content(
                model=self.model,
                contents=f"{system_prompt}\n\n{user_prompt}",
                config={
                    "response_mime_type": "application/json",
                    "response_schema": response_schema,
                },
            )
            return response.text

        # google-genai's generate_content call is synchronous, so keep it off
        # FastAPI's event loop while preserving our async provider interface.
        content = await asyncio.to_thread(generate)

        if not content:
            raise RuntimeError("Gemini returned an empty response.")

        import json

        try:
            generated = json.loads(content)
        except json.JSONDecodeError as exc:
            raise RuntimeError("Gemini returned invalid JSON.") from exc

        required_keys = {
            "title",
            "hook",
            "script",
            "caption",
            "hashtags",
            "cta",
            "content_ideas",
        }
        missing = required_keys - generated.keys()
        if missing:
            raise RuntimeError(
                f"Gemini response is missing required fields: {', '.join(sorted(missing))}."
            )

        if not isinstance(generated["hashtags"], list):
            raise RuntimeError("Gemini returned hashtags in an invalid format.")
        if not isinstance(generated["content_ideas"], list) or len(generated["content_ideas"]) != 5:
            raise RuntimeError("Gemini must return exactly 5 content ideas.")

        return generated
    async def generate_storyboard(self, content: dict) -> dict:
        system_prompt = """
You are an expert short-form video director and storyboard artist.

Turn the supplied short-form video content into a practical scene-by-scene storyboard
for production using stock footage, still images, text overlays and later AI voice-over.

Return ONLY JSON with exactly these keys:
- title: storyboard title
- description: one-sentence production direction
- scenes: ordered array of scenes

Each scene must contain exactly these keys:
- scene_order: integer starting at 1
- title: short scene label
- narration: spoken voice-over for this scene
- visual_description: specific visual direction/search concept for stock media
- duration_seconds: number greater than 0
- transition: one of cut, dissolve, fade, slide, zoom

Rules:
- The first scene must immediately deliver the hook.
- The final scene must clearly deliver the CTA.
- Keep narration faithful to the supplied script and do not invent unsupported facts.
- Use enough scenes to keep the pacing engaging, normally 4 to 8 scenes.
- The total scene duration should closely match the requested video duration.
- Visual descriptions must be concrete enough to use later as stock-media search queries.
- Do not include markdown or commentary outside the JSON.
""".strip()

        user_prompt = f"""
Topic: {content['topic']}
Title: {content['title']}
Hook: {content['hook']}
Script: {content['script']}
CTA: {content['cta']}
Style: {content['style']}
Platform: {content['platform']}
Target duration: {content['duration']} seconds
Target audience: {content['target_audience']}
""".strip()

        scene_schema = {
            "type": "object",
            "properties": {
                "scene_order": {"type": "integer"},
                "title": {"type": "string"},
                "narration": {"type": "string"},
                "visual_description": {"type": "string"},
                "duration_seconds": {"type": "number"},
                "transition": {
                    "type": "string",
                    "enum": ["cut", "dissolve", "fade", "slide", "zoom"],
                },
            },
            "required": [
                "scene_order",
                "title",
                "narration",
                "visual_description",
                "duration_seconds",
                "transition",
            ],
        }

        response_schema = {
            "type": "object",
            "properties": {
                "title": {"type": "string"},
                "description": {"type": "string"},
                "scenes": {
                    "type": "array",
                    "items": scene_schema,
                    "minItems": 3,
                    "maxItems": 10,
                },
            },
            "required": ["title", "description", "scenes"],
        }

        def generate() -> str | None:
            response = self.client.models.generate_content(
                model=self.model,
                contents=f"{system_prompt}\n\n{user_prompt}",
                config={
                    "response_mime_type": "application/json",
                    "response_schema": response_schema,
                },
            )
            return response.text

        raw = await asyncio.to_thread(generate)
        if not raw:
            raise RuntimeError("Gemini returned an empty storyboard response.")

        import json

        try:
            storyboard = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise RuntimeError("Gemini returned invalid storyboard JSON.") from exc

        scenes = storyboard.get("scenes")
        if not isinstance(scenes, list) or len(scenes) < 3:
            raise RuntimeError("Gemini returned an invalid storyboard scene list.")

        # Normalize order and keep scene duration within model/database limits.
        for index, scene in enumerate(scenes, start=1):
            scene["scene_order"] = index
            try:
                scene["duration_seconds"] = max(0.5, min(float(scene["duration_seconds"]), 180.0))
            except (TypeError, ValueError, KeyError) as exc:
                raise RuntimeError("Gemini returned an invalid scene duration.") from exc

        return storyboard

