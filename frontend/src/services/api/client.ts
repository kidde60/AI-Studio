const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL || "http://localhost:8000/api/v1";

const TOKEN_KEY = "ai_video_studio_access_token";

export function getAccessToken() {
  return localStorage.getItem(TOKEN_KEY);
}
export function setAccessToken(token: string) {
  localStorage.setItem(TOKEN_KEY, token);
}
export function clearAccessToken() {
  localStorage.removeItem(TOKEN_KEY);
}

export async function apiRequest<T>(path: string, options: RequestInit = {}): Promise<T> {
  const headers = new Headers(options.headers);
  headers.set("Content-Type", "application/json");
  const token = getAccessToken();
  if (token) headers.set("Authorization", `Bearer ${token}`);

  let response: Response;
  try {
    response = await fetch(`${API_BASE_URL}${path}`, { ...options, headers });
  } catch {
    throw new Error("Could not connect to the backend. Make sure the API server is running and try again.");
  }

  if (!response.ok) {
    let message = `The request could not be completed (error ${response.status}).`;
    try {
      const body = await response.json();
      if (typeof body.detail === "string" && body.detail.trim()) {
        message = body.detail;
      }
    } catch {
      // Keep the user-friendly fallback when the server did not return JSON.
    }
    throw new Error(message);
  }
  if (response.status === 204) return undefined as T;
  return response.json() as Promise<T>;
}
