import apiClient from './client';

/**
 * Convert a server-side screenshot file path to a URL accessible via the static file server.
 *
 * Server paths look like: /tmp/w4agent/screenshots/abc123.png
 * The static mount serves from: /static/screenshots/
 */
export function getScreenshotUrl(serverPath: string | null | undefined): string | null {
  if (!serverPath) return null;

  // Extract the filename from the full server path
  const filename = serverPath.split('/').pop();
  if (!filename) return null;

  return `/static/screenshots/${filename}`;
}

/**
 * Trigger a browser file download from a blob response.
 */
function downloadBlob(data: Blob, filename: string): void {
  const url = window.URL.createObjectURL(new Blob([data]));
  const link = document.createElement('a');
  link.href = url;
  link.download = filename;
  document.body.appendChild(link);
  link.click();
  link.remove();
  window.URL.revokeObjectURL(url);
}

/**
 * Download a single page screenshot.
 */
export async function downloadPageScreenshot(pageId: string, annotated: boolean = false): Promise<void> {
  const response = await apiClient.get(`/pages/${pageId}/screenshot`, {
    params: { annotated },
    responseType: 'blob',
  });

  const disposition = response.headers['content-disposition'];
  const match = disposition?.match(/filename="?(.+?)"?$/);
  const filename = match?.[1] || `screenshot_${pageId}.png`;

  downloadBlob(response.data, filename);
}

/**
 * Download all screenshots for a task as a ZIP archive.
 */
export async function downloadTaskScreenshots(taskId: string, annotated: boolean = true): Promise<void> {
  const response = await apiClient.get(`/pages/task/${taskId}/screenshots/download`, {
    params: { annotated },
    responseType: 'blob',
    timeout: 120000, // ZIP generation may take longer
  });

  downloadBlob(response.data, `screenshots_${taskId}.zip`);
}
