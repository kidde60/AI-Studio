import json

from openai import AsyncOpenAI

from app.core.config import get_settings
from app.schemas.content import ContentGenerationRequest
from app.services.ai.base import AIContentProvider


class OpenAIContentProvider(AIContentProvider):
    def __init__(self) -> None:
        settings = get_settings()
        if not settings.openai_api_key:
            raise RuntimeError("OPENAI_API_KEY is not configured.")
        self.client = AsyncOpenAI(api_key=settings.openai_api_key)
        self.model = settings.openai_model

    async def generate_content(self, request: ContentGenerationRequest) -> dict:
        system_prompt = """
You are an expert short-form video content strategist.
Return ONLY valid JSON with these keys:
title, hook, script, caption, hashtags, cta, content_ideas.

Rules:
- Write concise, engaging social video content.
- Match the requested style, platform, duration and audience.
- hashtags must be an array of strings beginning with #.
- content_ideas must be an array of exactly 5 strings.
- script should be natural for voice-over.
"""

        user_prompt = f"""
Topic: {request.topic}
Style: {request.style}
Platform: {request.platform}
Duration: {request.duration} seconds
Target audience: {request.target_audience}
"""

        response = await self.client.chat.completions.create(
            model=self.model,
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
        )

        content = response.choices[0].message.content
        if not content:
            raise RuntimeError("AI provider returned an empty response.")

        return json.loads(content)

