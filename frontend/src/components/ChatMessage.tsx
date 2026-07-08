import { useState, type ReactNode } from "react";
import { Bot, Copy, Check, User, FileText } from "lucide-react";
import type { AppSettings } from "@/hooks/useSettings";

export interface Message {
  role: "user" | "assistant";
  content: string;
  sources?: Array<{ page: number; excerpt: string }>;
  timestamp?: string;
}

interface ChatMessageProps {
  message: Message;
  settings: Pick<AppSettings, "showTimestamps" | "showSources" | "compactMode">;
}

function formatContent(content: string) {
  const lines = content.split("\n");
  const blocks: ReactNode[] = [];
  let bulletBuffer: string[] = [];
  let key = 0;

  const flushBullets = () => {
    if (bulletBuffer.length === 0) return;
    blocks.push(
      <ul key={key++} className="msg-list">
        {bulletBuffer.map((item, i) => (
          <li key={i}>{item}</li>
        ))}
      </ul>
    );
    bulletBuffer = [];
  };

  for (const line of lines) {
    const trimmed = line.trim();
    const isBullet = /^[-•*]\s+/.test(trimmed);

    if (isBullet) {
      bulletBuffer.push(trimmed.replace(/^[-•*]\s+/, ""));
    } else {
      flushBullets();
      if (trimmed) {
        blocks.push(
          <p key={key++} className="msg-paragraph">
            {trimmed}
          </p>
        );
      }
    }
  }
  flushBullets();

  if (blocks.length === 0) {
    return <p className="msg-paragraph">{content}</p>;
  }
  return <>{blocks}</>;
}

export const ChatMessage = ({ message, settings }: ChatMessageProps) => {
  const [copied, setCopied] = useState(false);
  const isUser = message.role === "user";

  const handleCopy = async () => {
    await navigator.clipboard.writeText(message.content);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <article
      className={`msg-card msg-card--${message.role}${settings.compactMode ? " msg-card--compact" : ""}`}
    >
      <div className="msg-card-accent" aria-hidden />

      <header className="msg-card-header">
        <div className="msg-card-identity">
          <div className={`msg-card-icon msg-card-icon--${message.role}`}>
            {isUser ? <User size={14} /> : <Bot size={14} />}
          </div>
          <div className="msg-card-meta">
            <span className="msg-card-name">{isUser ? "You" : "Study Buddy"}</span>
            {settings.showTimestamps && message.timestamp && (
              <span className="msg-card-time">{message.timestamp}</span>
            )}
          </div>
        </div>

        {!isUser && (
          <button
            className="msg-copy-btn"
            onClick={handleCopy}
            title="Copy response"
            aria-label="Copy response"
          >
            {copied ? <Check size={13} /> : <Copy size={13} />}
          </button>
        )}
      </header>

      <div className="msg-card-body">{formatContent(message.content)}</div>

      {!isUser && settings.showSources && message.sources && message.sources.length > 0 && (
        <footer className="msg-card-footer">
          <span className="msg-footer-label">Sources</span>
          <div className="msg-source-list">
            {message.sources.map((src, i) => (
              <button
                key={i}
                className="msg-source-chip"
                title={src.excerpt}
                type="button"
              >
                <FileText size={11} />
                Page {src.page}
              </button>
            ))}
          </div>
        </footer>
      )}
    </article>
  );
};

export const TypingMessage = ({ compactMode }: { compactMode: boolean }) => (
  <article className={`msg-card msg-card--assistant msg-card--typing${compactMode ? " msg-card--compact" : ""}`}>
    <div className="msg-card-accent" aria-hidden />
    <header className="msg-card-header">
      <div className="msg-card-identity">
        <div className="msg-card-icon msg-card-icon--assistant">
          <Bot size={14} />
        </div>
        <div className="msg-card-meta">
          <span className="msg-card-name">Study Buddy</span>
          <span className="msg-card-time msg-card-time--live">Thinking…</span>
        </div>
      </div>
    </header>
    <div className="msg-card-body">
      <div className="typing-wave">
        <span /><span /><span />
      </div>
    </div>
  </article>
);
