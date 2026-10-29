
import type { ContentGenerationRequest, GeneratedContent } from "../../types/content";
import { apiRequest } from "./client";

interface ApiGeneratedContent {
  id: string;
  topic: string;
  style: GeneratedContent["style"];
  platform: GeneratedContent["platform"];
  duration: number;
  target_audience: string;
  title: string;
  hook: string;
  script: string;
  caption: string;
  hashtags: string[];
  cta: string;
  content_ideas: string[];
}

function mapContent(response: ApiGeneratedContent): GeneratedContent {
  return {
    id: response.id,
    topic: response.topic,
    title: response.title,
    hook: response.hook,
    script: response.script,
    caption: response.caption,
    hashtags: response.hashtags,
    cta: response.cta,
    contentIdeas: response.content_ideas,
    style: response.style,
    platform: response.platform,
    duration: response.duration,
    targetAudience: response.target_audience,
  };
}

export async function generateContent(request: ContentGenerationRequest): Promise<GeneratedContent> {
  const response = await apiRequest<ApiGeneratedContent>("/content/generate", {
    method: "POST",
    body: JSON.stringify({
      topic: request.topic,
      style: request.style,
      platform: request.platform,
      duration: request.duration,
      target_audience: request.targetAudience,
    }),
  });
  return mapContent(response);
}

export async function updateContent(
  contentId: string,
  changes: Partial<{
    title: string;
    hook: string;
    script: string;
    caption: string;
    hashtags: string[];
    cta: string;
    content_ideas: string[];
  }>,
) {
  const response = await apiRequest<ApiGeneratedContent>(`/content/${contentId}`, {
    method: "PATCH",
    body: JSON.stringify(changes),
  });
  return mapContent(response);
}
