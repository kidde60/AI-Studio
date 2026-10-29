from app.schemas.content import ContentGenerationRequest
from app.services.ai.base import AIContentProvider


class MockContentProvider(AIContentProvider):
    async def generate_content(self, request: ContentGenerationRequest) -> dict:
        topic = request.topic.strip()
        clean_topic = "".join(ch for ch in topic if ch.isalnum() or ch == " ").strip()

        return {
            "title": f"What You Need to Know About {topic}",
            "hook": f"Most people are overlooking this important fact about {topic}.",
            "script": (
                f"If you've ever wondered about {topic}, this is for you.\n\n"
                f"Let's break it down in a simple and practical way. {topic} can make "
                "a real difference when you understand the basics and know what to do next.\n\n"
                "First, focus on the most important part: understand the problem you're "
                "trying to solve. Then identify the action that gives you the biggest "
                "result with the least unnecessary effort.\n\n"
                f"The key takeaway is simple: don't just consume information about {topic}. "
                "Turn what you learn into one clear action you can take today."
            ),
            "caption": (
                f"Here is a simple breakdown of {topic} you can actually use. "
                "Save this video and share it with someone who needs it."
            ),
            "hashtags": [
                f"#{clean_topic.replace(' ', '') or 'Content'}",
                "#ContentCreation",
                "#AITools",
                "#CreatorTips",
                "#LearnSomethingNew",
            ],
            "cta": "Follow for more practical tips and save this video for later.",
            "content_ideas": [
                f"3 mistakes people make with {topic}",
                f"A beginner's guide to {topic}",
                f"The fastest way to understand {topic}",
                f"{topic}: myths vs facts",
                f"5 practical tips for getting better results with {topic}",
            ],
        }

