import { apiRequest, getAccessToken } from "./client";

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000/api/v1";

export interface SubtitleCue { start: number; end: number; text: string; }
export interface SceneSubtitle { scene_id: string; cues: SubtitleCue[]; srt_text: string; }
export interface ProjectMusic {
  project_id: string; has_music: boolean; file_name?: string | null;
  volume?: number | null; fade_in_seconds?: number | null; fade_out_seconds?: number | null;
}
export interface RenderJob {
  id: string; project_id: string; status: "queued" | "rendering" | "completed" | "failed";
  output_url?: string | null; error_message?: string | null;
}

export function generateSceneSubtitles(sceneId: string, force = false) {
  return apiRequest<SceneSubtitle>(`/production/scenes/${sceneId}/subtitles`, {
    method: "POST", body: JSON.stringify({ force }),
  });
}
export function getSceneSubtitles(sceneId: string) {
  return apiRequest<SceneSubtitle>(`/production/scenes/${sceneId}/subtitles`);
}
export function getProjectMusic(projectId: string) {
  return apiRequest<ProjectMusic>(`/production/projects/${projectId}/music`);
}
export async function uploadProjectMusic(projectId: string, file: File) {
  const token = getAccessToken();
  const form = new FormData(); form.append("file", file);
  const response = await fetch(`${API_BASE_URL}/production/projects/${projectId}/music`, {
    method: "POST", headers: token ? { Authorization: `Bearer ${token}` } : undefined, body: form,
  });
  if (!response.ok) {
    let message = `Music upload failed (${response.status})`;
    try { const body = await response.json(); message = body.detail || message; } catch {}
    throw new Error(message);
  }
  return response.json() as Promise<ProjectMusic>;
}
export function updateProjectMusic(projectId: string, settings: { volume: number; fade_in_seconds: number; fade_out_seconds: number }) {
  return apiRequest<ProjectMusic>(`/production/projects/${projectId}/music`, {
    method: "PATCH", body: JSON.stringify(settings),
  });
}
export function createRender(projectId: string, storyboardId: string, width = 1080, height = 1920) {
  return apiRequest<RenderJob>(`/production/projects/${projectId}/render`, {
    method: "POST", body: JSON.stringify({ storyboard_id: storyboardId, width, height, fps: 30 }),
  });
}
export function getRenderJob(jobId: string) { return apiRequest<RenderJob>(`/production/render/${jobId}`); }
export async function getRenderVideoUrl(jobId: string) {
  const token = getAccessToken();
  const response = await fetch(`${API_BASE_URL}/production/render/${jobId}/video`, { headers: token ? { Authorization: `Bearer ${token}` } : undefined });
  if (!response.ok) throw new Error("Could not load the rendered video.");
  return URL.createObjectURL(await response.blob());
}
