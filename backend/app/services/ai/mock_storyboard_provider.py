from app.services.ai.base import AIStoryboardProvider


class MockStoryboardProvider(AIStoryboardProvider):
    async def generate_storyboard(self, content: dict) -> dict:
        duration = float(content.get("duration", 45))
        scene_count = 5
        base = max(duration / scene_count, 1)
        return {
            "title": f"Storyboard: {content['title']}",
            "description": "A paced short-form storyboard generated from the supplied script.",
            "scenes": [
                {
                    "scene_order": 1,
                    "title": "Hook",
                    "narration": content["hook"],
                    "visual_description": f"Attention-grabbing opening visual about {content['topic']}",
                    "duration_seconds": base,
                    "transition": "cut",
                },
                {
                    "scene_order": 2,
                    "title": "Context",
                    "narration": content["script"][:300],
                    "visual_description": f"Contextual stock footage illustrating {content['topic']}",
                    "duration_seconds": base,
                    "transition": "cut",
                },
                {
                    "scene_order": 3,
                    "title": "Key Point",
                    "narration": "Highlight the central idea from the script.",
                    "visual_description": "Supporting close-up or demonstration footage for the key point",
                    "duration_seconds": base,
                    "transition": "dissolve",
                },
                {
                    "scene_order": 4,
                    "title": "Takeaway",
                    "narration": "Reinforce the practical takeaway for the viewer.",
                    "visual_description": "Positive result or outcome visual related to the topic",
                    "duration_seconds": base,
                    "transition": "cut",
                },
                {
                    "scene_order": 5,
                    "title": "CTA",
                    "narration": content["cta"],
                    "visual_description": "Simple branded end card with clear call-to-action text",
                    "duration_seconds": base,
                    "transition": "fade",
                },
            ],
        }
