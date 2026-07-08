import type { AuthSession, AuthUser } from "@/types/auth";

const API_BASE = (import.meta.env.VITE_API_URL || "http://127.0.0.1:5000").replace(/\/$/, "");
const SESSION_KEY = "studybuddy_auth_session";

export function getStoredSession(): AuthSession | null {
  try {
    const raw = localStorage.getItem(SESSION_KEY);
    return raw ? JSON.parse(raw) : null;
  } catch {
    return null;
  }
}

export function storeSession(session: AuthSession | null) {
  if (session) {
    localStorage.setItem(SESSION_KEY, JSON.stringify(session));
  } else {
    localStorage.removeItem(SESSION_KEY);
  }
}

async function parseError(response: Response): Promise<string> {
  try {
    const data = await response.json();
    return data.error || data.message || "Request failed.";
  } catch {
    return "Request failed.";
  }
}

async function authFetch(
  path: string,
  options: RequestInit = {},
  accessToken?: string | null
): Promise<Response> {
  const headers = new Headers(options.headers);
  if (options.body && !(options.body instanceof FormData) && !headers.has("Content-Type")) {
    headers.set("Content-Type", "application/json");
  }
  if (accessToken) {
    headers.set("Authorization", `Bearer ${accessToken}`);
  }

  return fetch(`${API_BASE}${path}`, { ...options, headers });
}

export async function register(email: string, password: string) {
  const response = await authFetch("/auth/register", {
    method: "POST",
    body: JSON.stringify({ email, password }),
  });
  const data = await response.json();
  if (!response.ok) {
    throw new Error(await parseError(response));
  }
  return data as {
    message: string;
    email_verification_required?: boolean;
    access_token?: string;
    refresh_token?: string;
    user?: AuthUser;
  };
}

export async function login(email: string, password: string): Promise<AuthSession> {
  const response = await authFetch("/auth/login", {
    method: "POST",
    body: JSON.stringify({ email, password }),
  });
  if (!response.ok) {
    throw new Error(await parseError(response));
  }
  return response.json();
}

export async function refreshSession(refreshToken: string): Promise<AuthSession> {
  const response = await authFetch("/auth/refresh", {
    method: "POST",
    body: JSON.stringify({ refresh_token: refreshToken }),
  });
  if (!response.ok) {
    throw new Error(await parseError(response));
  }
  return response.json();
}

export async function fetchMe(accessToken: string): Promise<AuthUser> {
  const response = await authFetch("/auth/me", {}, accessToken);
  if (!response.ok) {
    throw new Error(await parseError(response));
  }
  const data = await response.json();
  return data.user;
}

export async function verifyEmail(token: string): Promise<AuthSession> {
  const response = await authFetch("/auth/verify-email", {
    method: "POST",
    body: JSON.stringify({ token }),
  });
  if (!response.ok) {
    throw new Error(await parseError(response));
  }
  return response.json();
}

export async function resendVerification(email: string) {
  const response = await authFetch("/auth/resend-verification", {
    method: "POST",
    body: JSON.stringify({ email }),
  });
  if (!response.ok) {
    throw new Error(await parseError(response));
  }
  return response.json();
}

export async function forgotPassword(email: string) {
  const response = await authFetch("/auth/forgot-password", {
    method: "POST",
    body: JSON.stringify({ email }),
  });
  if (!response.ok) {
    throw new Error(await parseError(response));
  }
  return response.json();
}

export async function resetPassword(token: string, password: string): Promise<AuthSession> {
  const response = await authFetch("/auth/reset-password", {
    method: "POST",
    body: JSON.stringify({ token, password }),
  });
  if (!response.ok) {
    throw new Error(await parseError(response));
  }
  return response.json();
}

export function getOAuthUrl(provider: "google" | "github") {
  return `${API_BASE}/auth/oauth/${provider}`;
}

export { API_BASE };
