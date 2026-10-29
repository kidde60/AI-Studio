
import { getAccessToken, apiRequest } from "./client";

const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL || "http://localhost:8000/api/v1";

export interface UserAsset {
  id: string;
  project_id: string | null;
  file_name: string;
  asset_type: "image" | "video" | "audio";
  mime_type: string;
  size_bytes: number;
  file_url: string;
  created_at: string;
}

export async function uploadAsset(file: File, projectId?: string) {
  const form = new FormData();
  form.append("file", file);

  const query = projectId ? `?project_id=${encodeURIComponent(projectId)}` : "";
  const token = getAccessToken();
  const response = await fetch(`${API_BASE_URL}/assets/upload${query}`, {
    method: "POST",
    headers: token ? { Authorization: `Bearer ${token}` } : undefined,
    body: form,
  });

  if (!response.ok) {
    let message = `Upload failed with status ${response.status}`;
    try {
      const body = await response.json();
      message = body.detail || message;
    } catch {}
    throw new Error(message);
  }
  return response.json() as Promise<UserAsset>;
}

export function listAssets(params?: { assetType?: UserAsset["asset_type"]; projectId?: string }) {
  const query = new URLSearchParams();
  if (params?.assetType) query.set("asset_type", params.assetType);
  if (params?.projectId) query.set("project_id", params.projectId);
  const suffix = query.toString() ? `?${query}` : "";
  return apiRequest<UserAsset[]>(`/assets${suffix}`);
}

export function deleteAsset(assetId: string) {
  return apiRequest<void>(`/assets/${assetId}`, { method: "DELETE" });
}

export function assetFileUrl(assetId: string) {
  const token = getAccessToken();
  return `${API_BASE_URL}/assets/${assetId}/file${token ? `?access_token=${encodeURIComponent(token)}` : ""}`;
}
