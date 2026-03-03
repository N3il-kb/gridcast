import { useEffect, useRef, useState } from "react";
import { useChat } from "@ai-sdk/react";

export default function GridAskWidget({ hexA, hexB, onClose }) {
  const bottomRef = useRef(null);
  const [text, setText] = useState("");

  const { messages, sendMessage, status, setMessages } = useChat({ api: "/api/chat" });
  const isLoading = status === "streaming" || status === "submitted";

  // Clear chat when hex selection changes
  useEffect(() => {
    setMessages([]);
  }, [hexA?.properties?.hex_id, hexB?.properties?.hex_id, setMessages]);

  // Auto-scroll to latest message
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const onSubmit = (e) => {
    e.preventDefault();
    const trimmed = text.trim();
    if (!trimmed || isLoading) return;
    setText("");
    sendMessage(
      { text: trimmed },
      { body: { hexA: hexA?.properties ?? null, hexB: hexB?.properties ?? null } },
    );
  };

  return (
    <div className="h-full w-full flex flex-col rounded-2xl border border-white/10 bg-[#0c1622]/95 text-sm shadow-2xl backdrop-blur-md overflow-hidden">
      {/* Header */}
      <div className="flex items-center justify-between px-4 py-3 border-b border-white/10 flex-shrink-0">
        <div className="flex items-center gap-2">
          <span className="text-xl drop-shadow-[0_0_8px_rgba(0,255,128,0.4)]" role="img" aria-label="Lightning">⚡</span>
          <span className="text-base font-bold tracking-tight text-white">GridAsk</span>
          <span className="text-[10px] font-mono text-neon bg-neon/10 border border-neon/20 rounded px-1.5 py-0.5 tracking-widest">
            AI
          </span>
        </div>
        <button
          onClick={onClose}
          className="rounded-lg px-2 py-0.5 text-xs text-white/40 transition hover:text-neon hover:drop-shadow-[0_0_8px_rgba(0,255,128,0.6)]"
        >
          ✕
        </button>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto px-4 py-3 space-y-3 min-h-0">
        {messages.length === 0 && (
          <p className="text-white/30 text-xs text-center mt-10 leading-relaxed">
            {hexA || hexB
              ? "Ask me anything about your selected hexagons."
              : "Select hexagons on the map, then ask me anything about the grid."}
          </p>
        )}

        {messages.map((m) => {
          const text = m.parts?.filter(p => p.type === "text").map(p => p.text).join("") ?? "";
          if (!text) return null;
          return (
            <div key={m.id} className={`flex ${m.role === "user" ? "justify-end" : "justify-start"}`}>
              <div
                className={`max-w-[86%] rounded-xl px-3 py-2 text-xs leading-relaxed ${
                  m.role === "user"
                    ? "bg-neon text-black font-medium"
                    : "bg-white/[0.07] text-white/85 border border-white/10"
                }`}
              >
                {text}
              </div>
            </div>
          );
        })}

        {isLoading && (
          <div className="flex justify-start">
            <div className="bg-white/[0.07] border border-white/10 rounded-xl px-3 py-2">
              <span className="text-neon/70 text-xs tracking-widest">···</span>
            </div>
          </div>
        )}

        <div ref={bottomRef} />
      </div>

      {/* Input */}
      <form onSubmit={onSubmit} className="px-3 py-3 border-t border-white/10 flex gap-2 flex-shrink-0">
        <input
          value={text}
          onChange={(e) => setText(e.target.value)}
          placeholder="Ask about the grid..."
          className="flex-1 bg-white/5 border border-white/10 rounded-lg px-3 py-2 text-xs text-white placeholder-white/30 focus:outline-none focus:border-neon/50 transition"
        />
        <button
          type="submit"
          disabled={isLoading || !text.trim()}
          className="bg-neon text-black text-xs font-bold px-3 py-2 rounded-lg hover:brightness-110 disabled:opacity-40 transition"
        >
          →
        </button>
      </form>
    </div>
  );
}
