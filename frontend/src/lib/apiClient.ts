export async function apiFetch(
  baseUrl: string,
  path: string,
  accessToken: string,
  options: RequestInit = {}
): Promise<Response> {
  const headers = new Headers(options.headers);

  if (accessToken) {
    headers.set("Authorization", `Bearer ${accessToken}`);
  }

  if (options.body && !(options.body instanceof FormData) && !headers.has("Content-Type")) {
    headers.set("Content-Type", "application/json");
  }

  return fetch(`${baseUrl.replace(/\/$/, "")}${path}`, {
    ...options,
    headers,
  });
}

export async function parseApiError(response: Response): Promise<string> {
  try {
    const data = await response.json();
    return data.error || data.message || "Request failed.";
  } catch {
    return "Request failed.";
  }
}
