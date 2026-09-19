import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import type { MessageOut } from "../lib/chatApi";

/**
 * A single chat bubble. User messages render plain; assistant messages
 * use react-markdown + remark-gfm to support lists / tables / code blocks.
 *
 * Tailwind v4 design tokens (muted / accent) are reused from the existing
 * study-pal palette so the chat blends into the Dashboard dark/light theme.
 */
export interface ChatMessageProps {
  message: MessageOut;
  isStreaming?: boolean;
}

export function ChatMessage({
  message,
  isStreaming = false,
}: ChatMessageProps) {
  const isUser = message.role === "user";
  const wrapperClass = isUser
    ? "ml-auto bg-accent text-background rounded-2xl rounded-br-sm px-4 py-2 max-w-[78%]"
    : "mr-auto bg-muted text-foreground rounded-2xl rounded-bl-sm px-4 py-2 max-w-[78%]";

  return (
    <div className={wrapperClass}>
      {isUser ? (
        <p className="whitespace-pre-wrap break-words leading-relaxed">
          {message.content}
        </p>
      ) : (
        <div className="prose prose-sm dark:prose-invert max-w-none">
          <ReactMarkdown
            remarkPlugins={[remarkGfm]}
            components={{
              // Drop raw HTML — react-markdown already excludes by default,
              // but be explicit to keep the spec's "XSS stripped" guarantee.
              html: () => null,
            }}
          >
            {message.content || (isStreaming ? "…" : "")}
          </ReactMarkdown>
        </div>
      )}
      {message.status === "incomplete" && (
        <p className="mt-1 text-xs text-foreground/60">（回答未完成）</p>
      )}
    </div>
  );
}