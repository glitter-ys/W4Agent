import apiClient from './client';
import type { Task, TaskCreate } from '../types/task';
import type { Issue } from '../types/a11y';

export async function getTasks(params?: {
  project_id?: string;
  status?: string;
  skip?: number;
  limit?: number;
}) {
  const { data } = await apiClient.get<{ items: Task[]; total: number }>('/tasks/', { params });
  return data;
}

export async function getTask(id: string) {
  const { data } = await apiClient.get<Task>(`/tasks/${id}`);
  return data;
}

export async function createTask(payload: TaskCreate) {
  const { data } = await apiClient.post<Task>('/tasks/', payload);
  return data;
}

export async function startTask(id: string) {
  const { data } = await apiClient.post<Task>(`/tasks/${id}/start`);
  return data;
}

export async function stopTask(id: string) {
  const { data } = await apiClient.post<Task>(`/tasks/${id}/stop`);
  return data;
}

export async function deleteTask(id: string) {
  await apiClient.delete(`/tasks/${id}`);
}

export async function getTaskIssues(taskId: string, params?: {
  severity?: string;
  status?: string;
  skip?: number;
  limit?: number;
}) {
  const { data } = await apiClient.get<{ items: Issue[]; total: number }>('/issues/', {
    params: { task_id: taskId, ...params },
  });
  return data;
}
