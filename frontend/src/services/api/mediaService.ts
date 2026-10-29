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
  files?: Array<{
    quality?: string;
    width?: number;
    height?: number;
    url?: string;
  }>;
}

export async function searchMedia(
  query: string,
  mediaType: "video" | "image" = "video",
  perPage = 6,
) {
  return apiRequest<{ query: string; media_type: string; results: MediaResult[] }>(
    "/media/search",
    {
      method: "POST",
      body: JSON.stringify({
        query,
        media_type: mediaType,
        per_page: perPage,
      }),
    },
  );
}
