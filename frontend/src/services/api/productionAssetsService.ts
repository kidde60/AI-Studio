import { apiRequest } from "./client";
import type { StoryboardScene } from "./storyboardService";

export interface AutoProductionSceneResult {
  scene_id: string;
  scene_order: number;
  media_attached: boolean;
  voice_attached: boolean;
  media?: Record<string, unknown> | null;
  voice?: Record<string, unknown> | null;
  skipped_media: boolean;
  skipped_voice: boolean;
  error?: string | null;
}

export interface AutoProductionResponse {
  storyboard_id: string;
  scenes: AutoProductionSceneResult[];
}

export function autoProductionAssets(storyboardId: string) {
  return apiRequest<AutoProductionResponse>(`/production-assets/${storyboardId}/auto`, { method: "POST" });
}

export function updateScene(sceneId: string, data: Partial<Pick<StoryboardScene, "title" | "narration" | "visual_description" | "duration_seconds" | "transition">>) {
  return apiRequest<StoryboardScene>(`/production-assets/scenes/${sceneId}`, {
    method: "PATCH",
    body: JSON.stringify(data),
  });
}

export interface ProductionReadiness {
  storyboard_id: string;
  total_scenes: number;
  media_ready: number;
  voice_ready: number;
  subtitles_ready: number;
  ready_scenes: number;
  missing_scenes: Array<{
    scene_id: string;
    scene_order: number;
    media: boolean;
    voice: boolean;
    subtitles: boolean;
  }>;
  music_attached: boolean;
}

export function getProductionReadiness(storyboardId: string) {
  return apiRequest<ProductionReadiness>(`/production-assets/${storyboardId}/readiness`);
}
