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
