"use client";

import { useEffect, useRef } from "react";
import { useChatStream } from "../hooks/useChatStream";
import { ChatMessage } from "../components/ChatMessage";
import { ChatInput } from "../components/ChatInput";

export default function Home() {
  const { messages, status, sendMessage, approveToolCall } = useChatStream();
  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const isDisabled = status === "streaming" || status === "awaiting_approval";

  return (
    <div className="flex h-screen flex-col">
      <header className="border-b border-gray-200 px-6 py-4">
        <h1 className="text-lg font-semibold text-gray-900">aigent</h1>
        <p className="text-sm text-gray-500">Product search assistant</p>
      </header>

      <div className="flex-1 overflow-y-auto px-6 py-4">
        {messages.length === 0 && (
          <div className="flex h-full items-center justify-center">
            <p className="text-gray-400">
              Ask me to find products, compare prices, or check reviews.
            </p>
          </div>
        )}

        {messages.map((msg) => (
          <ChatMessage
            key={msg.id}
            message={msg}
            onApprove={() => approveToolCall(true)}
            onDeny={() => approveToolCall(false)}
          />
        ))}

        <div ref={messagesEndRef} />
      </div>

      <div className="border-t border-gray-200 px-6 py-4">
        <ChatInput onSend={sendMessage} disabled={isDisabled} />
        {status === "streaming" && (
          <p className="mt-2 text-xs text-gray-400">Agent is thinking...</p>
        )}
        {status === "awaiting_approval" && (
          <p className="mt-2 text-xs text-amber-600">
            Waiting for your approval to run the tool above.
          </p>
        )}
      </div>
    </div>
  );
}
