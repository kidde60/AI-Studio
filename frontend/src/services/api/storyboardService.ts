import { apiRequest } from "./client";

export interface MediaResult {
  provider: string;
  id: string;
  type: "video" | "image";
  url?: string;
  thumbnail?: string;
  duration?: number;
  width?: number;
  height?: number;
  title?: string;
  description?: string;
  source?: string;
  selection_source?: "auto" | "user_selected" | "stock_manual";
  manual_selection?: boolean;
  files?: Array<{ quality?: string; width?: number; height?: number; url?: string }>;
}

export interface StoryboardScene {
  id: string;
  storyboard_id: string;
  scene_order: number;
  title: string;
  narration: string | null;
  visual_description: string | null;
  duration_seconds: number;
  transition: string;
  media_asset_ids: MediaResult[];
}

export interface Storyboard {
  id: string;
  project_id: string;
  title: string;
  description: string | null;
  status: string;
  scenes: StoryboardScene[];
}

export function generateStoryboard(projectId: string, contentId: string) {
  return apiRequest<Storyboard>(`/storyboards/projects/${projectId}/generate`, {
    method: "POST",
    body: JSON.stringify({ content_id: contentId }),
  });
}

export function getStoryboard(storyboardId: string) {
  return apiRequest<Storyboard>(`/storyboards/${storyboardId}`);
}

export function listStoryboards(projectId: string) {
  return apiRequest<Storyboard[]>(`/storyboards/projects/${projectId}`);
}

export function searchSceneMedia(storyboardId: string, sceneId: string) {
  return apiRequest<{ scene_id: string; query: string; media_type: string; results: MediaResult[] }>(
    `/storyboards/${storyboardId}/scenes/${sceneId}/media/search`,
    { method: "POST", body: JSON.stringify({}) },
  );
}

export function selectSceneMedia(storyboardId: string, sceneId: string, media: MediaResult) {
  return apiRequest<{ scene: StoryboardScene }>(
    `/storyboards/${storyboardId}/scenes/${sceneId}/media/select`,
    { method: "POST", body: JSON.stringify({ media }) },
  );
}

export function selectUserAsset(storyboardId: string, sceneId: string, assetId: string) {
  return apiRequest<{ scene: StoryboardScene }>(
    `/storyboards/${storyboardId}/scenes/${sceneId}/media/user-select`,
    { method: "POST", body: JSON.stringify({ asset_id: assetId }) },
  );
}
