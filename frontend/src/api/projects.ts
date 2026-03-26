import apiClient from './client';
import type { Project, ProjectCreate } from '../types/project';

export async function getProjects(skip = 0, limit = 20) {
  const { data } = await apiClient.get<{ items: Project[]; total: number }>('/projects/', {
    params: { skip, limit },
  });
  return data;
}

export async function getProject(id: string) {
  const { data } = await apiClient.get<Project>(`/projects/${id}`);
  return data;
}

export async function createProject(payload: ProjectCreate) {
  const { data } = await apiClient.post<Project>('/projects/', payload);
  return data;
}

export async function updateProject(id: string, payload: Partial<ProjectCreate>) {
  const { data } = await apiClient.patch<Project>(`/projects/${id}`, payload);
  return data;
}

export async function deleteProject(id: string) {
  await apiClient.delete(`/projects/${id}`);
}
