"use client";

import { useState, FormEvent } from "react";

interface Props {
  onSend: (content: string) => void;
  disabled: boolean;
}

export function ChatInput({ onSend, disabled }: Props) {
  const [input, setInput] = useState("");
  const [isFocused, setIsFocused] = useState(false);

  const handleSubmit = (e: FormEvent) => {
    e.preventDefault();
    const trimmed = input.trim();
    if (!trimmed || disabled) return;
    onSend(trimmed);
    setInput("");
  };

  const hasText = input.trim().length > 0;

  return (
    <form onSubmit={handleSubmit}>
      <div
        className="flex items-center rounded-2xl px-4 py-2 transition-all duration-200"
        style={{
          background: "var(--bg-elevated)",
          border: "1px solid",
          borderColor: isFocused ? "var(--accent)" : "var(--border)",
          boxShadow: isFocused
            ? "0 0 0 3px var(--accent-glow)"
            : "var(--shadow-sm)",
        }}
      >
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onFocus={() => setIsFocused(true)}
          onBlur={() => setIsFocused(false)}
          placeholder="Search for a product..."
          disabled={disabled}
          className="flex-1 bg-transparent py-1.5 text-sm focus:outline-none disabled:opacity-40"
          style={{ color: "var(--text-primary)" }}
        />
        <button
          type="submit"
          disabled={disabled || !hasText}
          className="ml-2 flex h-9 w-9 shrink-0 items-center justify-center rounded-xl text-white transition-all duration-150 hover:scale-[1.04] active:scale-[0.96] disabled:opacity-30 disabled:hover:scale-100"
          style={{
            background: hasText ? "var(--accent)" : "var(--border)",
          }}
        >
          <svg
            className="h-4 w-4"
            fill="none"
            viewBox="0 0 24 24"
            strokeWidth={2.5}
            stroke="currentColor"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              d="M4.5 10.5L12 3m0 0l7.5 7.5M12 3v18"
            />
          </svg>
        </button>
      </div>
      {isFocused && !hasText && (
        <p
          className="mt-1.5 text-center text-[11px] animate-fade-in"
          style={{ color: "var(--text-muted)" }}
        >
          Press Enter to send
        </p>
      )}
    </form>
  );
}
