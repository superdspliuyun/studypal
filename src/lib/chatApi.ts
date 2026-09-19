/**
 * Chat API client. All endpoints are JWT-protected; the access token is
 * read from localStorage at call time so a logout / refresh invalidates
 * stale callers automatically.
 */

const BASE: string =
  (import.meta.env.VITE_API_BASE as string | undefined) ?? "";

const TOKEN_KEY = "studypal_access_token";

function readToken(): string {
  return localStorage.getItem(TOKEN_KEY) ?? "";
}

function authHeaders(): Record<string, string> {
  const t = readToken();
  return t ? { Authorization: `Bearer ${t}` } : {};
}

async function jsonOrThrow<T>(res: Response): Promise<T> {
  if (!res.ok) {
    const text = await res.text();
    throw new Error(text || `HTTP ${res.status}`);
  }
  return (await res.json()) as T;
}

export interface SessionListItem {
  session_id: number;
  created_at: string;
  updated_at: string;
  preview: string;
}

export interface SessionOut {
  session_id: number;
  user_id: number;
  created_at: string;
  updated_at: string;
}

export interface MessageOut {
  message_id: number;
  role: "user" | "assistant";
  content: string;
  status: "complete" | "incomplete";
  created_at: string;
}

export async function listSessions(): Promise<SessionListItem[]> {
  const res = await fetch(`${BASE}/api/chat/sessions`, {
    headers: { ...authHeaders() },
  });
  return jsonOrThrow<SessionListItem[]>(res);
}

export async function createSession(): Promise<SessionOut> {
  const res = await fetch(`${BASE}/api/chat/sessions`, {
    method: "POST",
    headers: { ...authHeaders() },
  });
  return jsonOrThrow<SessionOut>(res);
}

export async function listMessages(
  sessionId: number,
): Promise<MessageOut[]> {
  const res = await fetch(`${BASE}/api/chat/sessions/${sessionId}/messages`, {
    headers: { ...authHeaders() },
  });
  return jsonOrThrow<MessageOut[]>(res);
}

export interface DeltaEvent {
  message_id?: number;
  role?: "assistant";
  delta?: string;
}

export interface DoneEvent {
  message_id: number;
  status: "complete" | "incomplete";
}

/**
 * Send a user message and stream the assistant reply via SSE.
 *
 * Returns an AbortController so the caller can cancel mid-stream.
 * onDelta is invoked for every `data:` chunk with a delta field; the
 * caller accumulates the deltas into the assistant message body.
 */
export function sendMessageStream(
  sessionId: number,
  content: string,
  onDelta: (evt: DeltaEvent) => void,
  onDone: (evt: DoneEvent) => void,
  onError: (detail: string) => void,
): AbortController {
  const controller = new AbortController();
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    Accept: "text/event-stream",
    ...authHeaders(),
  };

  void (async () => {
    try {
      const res = await fetch(
        `${BASE}/api/chat/sessions/${sessionId}/messages`,
        {
          method: "POST",
          headers,
          body: JSON.stringify({ content }),
          signal: controller.signal,
        },
      );

      if (!res.ok) {
        onError(`HTTP ${res.status}: ${await res.text()}`);
        return;
      }
      if (!res.body) {
        onError("no response body");
        return;
      }

      const reader = res.body.getReader();
      const decoder = new TextDecoder();
      let buffer = "";
      let currentEvent = "message";

      while (true) {
        const { value, done } = await reader.read();
        if (done) break;
        buffer += decoder.decode(value, { stream: true });

        let idx: number;
        // eslint-disable-next-line no-cond-assign
        while ((idx = buffer.indexOf("\n\n")) !== -1) {
          const rawEvent = buffer.slice(0, idx);
          buffer = buffer.slice(idx + 2);
          currentEvent = "message";
          for (const line of rawEvent.split("\n")) {
            if (line.startsWith("event:")) {
              currentEvent = line.slice(6).trim();
            } else if (line.startsWith("data:")) {
              const payload = line.slice(5).trim();
              try {
                const parsed = JSON.parse(payload);
                if (currentEvent === "done") {
                  onDone(parsed as DoneEvent);
                } else if (currentEvent === "error") {
                  onError(parsed.detail ?? "unknown error");
                } else if (parsed.delta) {
                  onDelta(parsed as DeltaEvent);
                }
              } catch {
                /* ignore malformed chunks */
              }
            }
          }
        }
      }
    } catch (err) {
      if ((err as Error).name === "AbortError") return;
      onError((err as Error).message || String(err));
    }
  })();

  return controller;
}