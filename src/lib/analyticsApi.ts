/**
 * Analytics API client. Mirrors chatApi.ts style: reads base URL from
 * VITE_API_BASE and token from localStorage at call time.
 */

const BASE: string =
  (import.meta.env.VITE_API_BASE as string | undefined) ?? "";

const TOKEN_KEY = "studypal_access_token";

function authHeaders(): Record<string, string> {
  const t = localStorage.getItem(TOKEN_KEY) ?? "";
  return t ? { Authorization: `Bearer ${t}` } : {};
}

async function jsonOrThrow<T>(res: Response): Promise<T> {
  if (!res.ok) {
    throw new Error(await res.text());
  }
  return (await res.json()) as T;
}

export interface CalendarDay {
  date: string;
  minutes: number;
}

export interface Achievement {
  id: string;
  title: string;
  description: string;
  unlocked: boolean;
  progress: number;
  target: number;
}

export async function getCalendar(days: 30 | 60 | 90 | 180): Promise<CalendarDay[]> {
  const res = await fetch(
    `${BASE}/api/analytics/calendar?days=${days}`,
    { headers: { ...authHeaders() } },
  );
  return jsonOrThrow<CalendarDay[]>(res);
}

export async function getAchievements(): Promise<Achievement[]> {
  const res = await fetch(`${BASE}/api/analytics/achievements`, {
    headers: { ...authHeaders() },
  });
  return jsonOrThrow<Achievement[]>(res);
}

export function currentStreakDays(days: CalendarDay[]): number {
  let n = 0;
  for (let i = days.length - 1; i >= 0; i--) {
    if (days[i].minutes > 0) n++;
    else break;
  }
  return n;
}