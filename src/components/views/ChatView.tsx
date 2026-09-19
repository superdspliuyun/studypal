import { useEffect, useRef, useState } from 'react';
import { ChatMessage } from '../ChatMessage';
import {
  type MessageOut,
  createSession,
  listMessages,
  listSessions,
  sendMessageStream,
} from '../../lib/chatApi';

interface ChatViewProps {
  accessToken: string | null;
}

const AUTO_SCROLL_THRESHOLD_PX = 64;

interface ChatMessageUI extends MessageOut {
  isStreaming?: boolean;
}

export default function ChatView({ accessToken }: ChatViewProps) {
  const [sessions, setSessions] = useState<
    { session_id: number; preview: string }[]
  >([]);
  const [activeSessionId, setActiveSessionId] = useState<number | null>(null);
  const [messages, setMessages] = useState<ChatMessageUI[]>([]);
  const [composer, setComposer] = useState('');
  const [streaming, setStreaming] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const controllerRef = useRef<AbortController | null>(null);
  const scrollRef = useRef<HTMLDivElement | null>(null);
  const isAtBottomRef = useRef(true);

  // Initial session bootstrap: pick latest, or create one.
  useEffect(() => {
    if (!accessToken) return;
    let cancelled = false;
    void (async () => {
      try {
        const existing = await listSessions();
        if (cancelled) return;
        setSessions(
          existing.map((s) => ({
            session_id: s.session_id,
            preview: s.preview,
          })),
        );
        if (existing.length > 0) {
          setActiveSessionId(existing[0].session_id);
        } else {
          const fresh = await createSession();
          if (cancelled) return;
          setSessions([{ session_id: fresh.session_id, preview: '' }]);
          setActiveSessionId(fresh.session_id);
        }
      } catch (err) {
        if (!cancelled) setError((err as Error).message);
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [accessToken]);

  // Load messages when active session changes.
  useEffect(() => {
    if (activeSessionId === null) {
      setMessages([]);
      return;
    }
    let cancelled = false;
    void (async () => {
      try {
        const list = await listMessages(activeSessionId);
        if (!cancelled) setMessages(list);
      } catch (err) {
        if (!cancelled) setError((err as Error).message);
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [activeSessionId]);

  // Track whether the user is at (or near) the bottom — only auto-scroll then.
  useEffect(() => {
    const el = scrollRef.current;
    if (!el) return;
    const onScroll = () => {
      const distance = el.scrollHeight - el.scrollTop - el.clientHeight;
      isAtBottomRef.current = distance <= AUTO_SCROLL_THRESHOLD_PX;
    };
    el.addEventListener('scroll', onScroll);
    return () => el.removeEventListener('scroll', onScroll);
  }, []);

  // Auto-scroll on new message when user is at the bottom.
  useEffect(() => {
    if (!isAtBottomRef.current) return;
    const el = scrollRef.current;
    if (el) {
      el.scrollTo({ top: el.scrollHeight, behavior: 'smooth' });
    }
  }, [messages]);

  const handleSend = () => {
    const text = composer.trim();
    if (!text || streaming || activeSessionId === null) return;
    setError(null);
    setComposer('');

    const optimisticUser: ChatMessageUI = {
      message_id: -Date.now(),
      role: 'user',
      content: text,
      status: 'complete',
      created_at: new Date().toISOString(),
    };
    const assistantId = -Date.now() - 1;
    const optimisticAssistant: ChatMessageUI = {
      message_id: assistantId,
      role: 'assistant',
      content: '',
      status: 'incomplete',
      created_at: new Date().toISOString(),
      isStreaming: true,
    };
    setMessages((prev) => [...prev, optimisticUser, optimisticAssistant]);
    setStreaming(true);

    const controller = sendMessageStream(
      activeSessionId,
      text,
      (evt) => {
        setMessages((prev) =>
          prev.map((m) =>
            m.message_id === assistantId
              ? { ...m, content: m.content + (evt.delta ?? '') }
              : m,
          ),
        );
      },
      (done) => {
        setMessages((prev) =>
          prev.map((m) =>
            m.message_id === assistantId
              ? { ...m, status: 'complete', isStreaming: false }
              : m,
          ),
        );
        // Reload history from server to grab the canonical message_ids.
        if (activeSessionId !== null) {
          void listMessages(activeSessionId).then((list) => setMessages(list));
        }
        setStreaming(false);
        controllerRef.current = null;
        void done; // silence unused
      },
      (detail) => {
        setMessages((prev) =>
          prev.map((m) =>
            m.message_id === assistantId
              ? { ...m, status: 'incomplete', isStreaming: false }
              : m,
          ),
        );
        setError(detail);
        setStreaming(false);
        controllerRef.current = null;
      },
    );
    controllerRef.current = controller;
  };

  const handleStop = () => {
    controllerRef.current?.abort();
    controllerRef.current = null;
    setStreaming(false);
    setMessages((prev) =>
      prev.map((m) =>
        m.isStreaming
          ? { ...m, status: 'incomplete', isStreaming: false }
          : m,
      ),
    );
  };

  if (!accessToken) {
    return (
      <section aria-label="AI 助手" className="p-6 text-foreground">
        <p className="text-foreground/70">请先登录后与助手对话。</p>
      </section>
    );
  }

  return (
    <section
      aria-label="AI 助手"
      className="flex h-[calc(100vh-9rem)] flex-col gap-3"
    >
      <header className="flex items-baseline justify-between">
        <h2 className="text-xl font-semibold text-foreground">AI 学习助手</h2>
        <span className="text-xs text-foreground/60">
          {sessions.length} 个会话
        </span>
      </header>

      {error && (
        <div
          role="alert"
          className="rounded-md border border-border bg-muted px-3 py-2 text-sm text-foreground"
        >
          {error}
        </div>
      )}

      <div
        ref={scrollRef}
        className="flex-1 overflow-y-auto rounded-lg border border-border bg-background/40 p-4"
      >
        {messages.length === 0 ? (
          <p className="text-foreground/60">开始对话吧，向助手提一个学习问题。</p>
        ) : (
          <ul className="flex flex-col gap-3">
            {messages.map((m) => (
              <li key={m.message_id}>
                <ChatMessage message={m} isStreaming={m.isStreaming} />
              </li>
            ))}
          </ul>
        )}
      </div>

      <form
        onSubmit={(e) => {
          e.preventDefault();
          handleSend();
        }}
        className="flex items-end gap-2"
      >
        <textarea
          value={composer}
          onChange={(e) => setComposer(e.target.value)}
          placeholder="向 AI 助手提问…"
          rows={2}
          className="flex-1 resize-none rounded-md border border-border bg-background px-3 py-2 text-foreground placeholder:text-foreground/40 focus:outline-none focus:ring-2 focus:ring-accent"
          onKeyDown={(e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
              e.preventDefault();
              handleSend();
            }
          }}
          disabled={streaming}
        />
        {streaming ? (
          <button
            type="button"
            onClick={handleStop}
            className="rounded-md bg-foreground px-4 py-2 text-background hover:bg-foreground/90"
          >
            停止
          </button>
        ) : (
          <button
            type="submit"
            className="rounded-md bg-accent px-4 py-2 text-background hover:bg-accent-hover disabled:opacity-50"
            disabled={!composer.trim()}
          >
            发送
          </button>
        )}
      </form>
    </section>
  );
}