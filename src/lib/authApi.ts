/**
 * Auth API client. Mirrors chatApi / analyticsApi style.
 * Stores access_token + refresh_token + user_id in localStorage on success.
 */

const BASE: string =
  (import.meta.env.VITE_API_BASE as string | undefined) ?? "";

const TOKEN_KEY = "studypal_access_token";
const REFRESH_KEY = "studypal_refresh_token";
const USER_ID_KEY = "studypal_user_id";
const EMAIL_KEY = "studypal_email";

export interface TokenPair {
  user_id: number;
  email: string;
  access_token: string;
  refresh_token: string;
  token_type: string;
}

export function getStoredToken(): string | null {
  return localStorage.getItem(TOKEN_KEY);
}

export function getStoredEmail(): string | null {
  return localStorage.getItem(EMAIL_KEY);
}

export function logout(): void {
  localStorage.removeItem(TOKEN_KEY);
  localStorage.removeItem(REFRESH_KEY);
  localStorage.removeItem(USER_ID_KEY);
  localStorage.removeItem(EMAIL_KEY);
  window.dispatchEvent(new Event("studypal:auth"));
}

function persist(pair: TokenPair): void {
  localStorage.setItem(TOKEN_KEY, pair.access_token);
  localStorage.setItem(REFRESH_KEY, pair.refresh_token);
  localStorage.setItem(USER_ID_KEY, String(pair.user_id));
  localStorage.setItem(EMAIL_KEY, pair.email);
  window.dispatchEvent(new Event("studypal:auth"));
}

async function jsonOrThrow<T>(res: Response): Promise<T> {
  const text = await res.text();
  if (!res.ok) {
    throw new Error(text || `HTTP ${res.status}`);
  }
  return JSON.parse(text) as T;
}

export async function register(
  email: string,
  password: string,
): Promise<TokenPair> {
  const res = await fetch(`${BASE}/api/auth/register`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email, password }),
  });
  const pair = await jsonOrThrow<TokenPair>(res);
  persist(pair);
  return pair;
}

export async function login(
  email: string,
  password: string,
): Promise<TokenPair> {
  const res = await fetch(`${BASE}/api/auth/login`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email, password }),
  });
  const pair = await jsonOrThrow<TokenPair>(res);
  persist(pair);
  return pair;
}

export async function refreshToken(): Promise<string | null> {
  const refresh = localStorage.getItem(REFRESH_KEY);
  if (!refresh) return null;
  try {
    const res = await fetch(`${BASE}/api/auth/refresh`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ refresh_token: refresh }),
    });
    if (!res.ok) {
      logout();
      return null;
    }
    const data = (await res.json()) as { access_token: string };
    localStorage.setItem(TOKEN_KEY, data.access_token);
    return data.access_token;
  } catch {
    logout();
    return null;
  }
}