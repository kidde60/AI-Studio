import { apiRequest } from "./client";

export interface Project {
  id: string;
  user_id: string;
  name: string;
  description: string | null;
  status: string;
  platform: string;
  duration: number;
}

export interface ProjectCreateInput {
  name: string;
  description: string | null;
  platform: string;
  duration: number;
}

export function createProject(data: ProjectCreateInput) {
  return apiRequest<Project>("/projects", {
    method: "POST",
    body: JSON.stringify(data),
  });
}

export function listProjects() {
  return apiRequest<Project[]>("/projects");
}

export function getProject(projectId: string) {
  return apiRequest<Project>(`/projects/${projectId}`);
}
