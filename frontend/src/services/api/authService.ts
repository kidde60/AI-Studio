import { apiRequest, clearAccessToken, setAccessToken } from "./client";

export interface User {
  id: string;
  email: string;
  full_name: string | null;
  is_active: boolean;
}
interface AuthResponse { access_token: string; token_type: string; user: User; }

export async function register(email: string, password: string, fullName?: string) {
  const r = await apiRequest<AuthResponse>("/auth/register", {
    method: "POST", body: JSON.stringify({ email, password, full_name: fullName }),
  });
  setAccessToken(r.access_token);
  return r.user;
}
export async function login(email: string, password: string) {
  const r = await apiRequest<AuthResponse>("/auth/login", {
    method: "POST", body: JSON.stringify({ email, password }),
  });
  setAccessToken(r.access_token);
  return r.user;
}
export function logout() { clearAccessToken(); }
export function me() { return apiRequest<User>("/auth/me"); }
