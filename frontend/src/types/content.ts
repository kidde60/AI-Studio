export type ContentStyle =
  | "Educational"
  | "Promotional"
  | "Entertainment"
  | "News"
  | "Storytelling";

export type Platform =
  | "TikTok"
  | "Instagram Reels"
  | "YouTube Shorts"
  | "Facebook";

export interface ContentGenerationRequest {
  topic: string;
  style: ContentStyle;
  platform: Platform;
  duration: number;
  targetAudience: string;
}

export interface GeneratedContent {
  id: string;
  topic: string;
  title: string;
  hook: string;
  script: string;
  caption: string;
  hashtags: string[];
  cta: string;
  contentIdeas: string[];
  style: ContentStyle;
  platform: Platform;
  duration: number;
  targetAudience: string;
}

export interface GenerationStatus {
  status: "idle" | "generating" | "success" | "error";
  message?: string;
}
