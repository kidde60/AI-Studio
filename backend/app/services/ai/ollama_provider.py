import json

import httpx

from app.core.config import get_settings
from app.schemas.content import ContentGenerationRequest
from app.services.ai.base import AIContentProvider, AIStoryboardProvider


class OllamaProvider(AIContentProvider, AIStoryboardProvider):
    """Generate content and storyboards through a locally running Ollama model."""

    def __init__(self) -> None:
        settings = get_settings()
        self.base_url = settings.ollama_base_url.rstrip("/")
        self.model = settings.ollama_model

    async def _generate_json(self, system_prompt: str, user_prompt: str) -> dict:
        try:
            async with httpx.AsyncClient(
                timeout=httpx.Timeout(300.0, connect=5.0)
            ) as client:
                response = await client.post(
                    f"{self.base_url}/api/chat",
                    json={
                        "model": self.model,
                        "messages": [
                            {"role": "system", "content": system_prompt},
                            {"role": "user", "content": user_prompt},
                        ],
                        "format": "json",
                        "stream": False,
                    },
                )
                response.raise_for_status()
        except httpx.ConnectError as exc:
            raise RuntimeError(
                f"Cannot connect to Ollama at {self.base_url}. "
                "Start Ollama and ensure the configured model is available."
            ) from exc

        try:
            content = response.json()["message"]["content"]
            result = json.loads(content)
        except (KeyError, TypeError, json.JSONDecodeError) as exc:
            raise RuntimeError("Ollama returned invalid JSON output.") from exc

        if not isinstance(result, dict):
            raise RuntimeError("Ollama output must be a JSON object.")
        return result

    async def generate_content(self, request: ContentGenerationRequest) -> dict:
        system_prompt = """
You are an expert short-form video content strategist and scriptwriter.
Return ONLY a JSON object with exactly these keys:
title, hook, script, caption, hashtags, cta, content_ideas.
Hashtags must be an array of strings beginning with #.
content_ideas must be an array of exactly 5 strings.
Match the requested style, platform, duration, and audience. Keep the script natural
for voice-over and avoid unsupported factual claims.
""".strip()
        user_prompt = (
            f"Topic: {request.topic}\n"
            f"Style: {request.style}\n"
            f"Platform: {request.platform}\n"
            f"Duration: {request.duration} seconds\n"
            f"Target audience: {request.target_audience}"
        )
        generated = await self._generate_json(system_prompt, user_prompt)

        required = {
            "title",
            "hook",
            "script",
            "caption",
            "hashtags",
            "cta",
            "content_ideas",
        }
        missing = required - generated.keys()
        if missing:
            raise RuntimeError(
                f"Ollama content is missing fields: {', '.join(sorted(missing))}."
            )
        if not isinstance(generated["hashtags"], list):
            raise RuntimeError("Ollama returned hashtags in an invalid format.")
        if (
            not isinstance(generated["content_ideas"], list)
            or len(generated["content_ideas"]) != 5
        ):
            raise RuntimeError("Ollama must return exactly 5 content ideas.")
        return generated

    async def generate_storyboard(self, content: dict) -> dict:
        system_prompt = """
You are an expert short-form video director and storyboard artist.
Return ONLY a JSON object with title, description, and scenes.
Each scene must contain scene_order, title, narration, visual_description,
duration_seconds, and transition. Use 3 to 10 scenes; transitions must be one of
cut, dissolve, fade, slide, or zoom. Keep narration faithful to the supplied script.
Visual descriptions should be concrete stock-media search concepts. The first scene
must deliver the hook and the final scene the CTA.
""".strip()
        user_prompt = (
            f"Topic: {content['topic']}\n"
            f"Title: {content['title']}\n"
            f"Hook: {content['hook']}\n"
            f"Script: {content['script']}\n"
            f"CTA: {content['cta']}\n"
            f"Style: {content['style']}\n"
            f"Platform: {content['platform']}\n"
            f"Target duration: {content['duration']} seconds\n"
            f"Target audience: {content['target_audience']}"
        )
        storyboard = await self._generate_json(system_prompt, user_prompt)
        scenes = storyboard.get("scenes")
        if not isinstance(scenes, list) or not 3 <= len(scenes) <= 10:
            raise RuntimeError("Ollama returned an invalid storyboard scene list.")

        allowed_transitions = {"cut", "dissolve", "fade", "slide", "zoom"}
        for index, scene in enumerate(scenes, start=1):
            if not isinstance(scene, dict):
                raise RuntimeError("Ollama returned an invalid storyboard scene.")
            try:
                duration = float(scene["duration_seconds"])
            except (KeyError, TypeError, ValueError) as exc:
                raise RuntimeError("Ollama returned an invalid scene duration.") from exc
            scene["scene_order"] = index
            scene["duration_seconds"] = max(0.5, min(duration, 180.0))
            if scene.get("transition") not in allowed_transitions:
                scene["transition"] = "cut"

        if not storyboard.get("title"):
            raise RuntimeError("Ollama storyboard is missing a title.")
        return storyboard
