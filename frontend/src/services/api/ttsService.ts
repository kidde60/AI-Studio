import { apiRequest, getAccessToken } from "./client";

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000/api/v1";

export interface SceneTTSResponse {
  scene_id: string;
  audio_url: string;
  voice: string;
  model: string;
  duration_seconds?: number | null;
}
export interface SceneTTSStatusResponse {
  scene_id: string;
  has_audio: boolean;
  audio_url?: string | null;
  voice?: string | null;
  model?: string | null;
  duration_seconds?: number | null;
}

export function generateSceneAudio(sceneId: string, voice = "Kore", forceRegenerate = false) {
  return apiRequest<SceneTTSResponse>(`/tts/scenes/${sceneId}/generate`, {
    method: "POST", body: JSON.stringify({ voice, force_regenerate: forceRegenerate }),
  });
}
export function getSceneAudioStatus(sceneId: string) { return apiRequest<SceneTTSStatusResponse>(`/tts/scenes/${sceneId}`); }
export async function getSceneAudioBlobUrl(sceneId: string): Promise<string> {
  const token = getAccessToken();
  const response = await fetch(`${API_BASE_URL}/tts/scenes/${sceneId}/audio`, { headers: token ? { Authorization: `Bearer ${token}` } : undefined });
  if (!response.ok) throw new Error("Could not load generated voice-over audio.");
  return URL.createObjectURL(await response.blob());
}
