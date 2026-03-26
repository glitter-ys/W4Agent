import apiClient from './client';
import type { Report } from '../types/report';

export async function getReportByTask(taskId: string) {
  const { data } = await apiClient.get<Report>(`/reports/task/${taskId}`);
  return data;
}

export async function exportReport(taskId: string, format: 'html' | 'pdf' | 'json') {
  const { data } = await apiClient.post(`/reports/task/${taskId}/export`, { format }, {
    responseType: 'blob',
  });
  return data;
}
