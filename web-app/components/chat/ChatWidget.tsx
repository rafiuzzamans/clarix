"use client";

import { useState, useRef, useEffect } from "react";
import { chatbotApi } from "@/lib/api";
import { useAuth } from "@/lib/auth-context";
import {
  Bot, Send, Loader2, X, Minus, RefreshCw,
} from "lucide-react";

interface Message {
  role: "user" | "assistant";
  content: string;
  timestamp: string;
}

const WELCOME: Message = {
  role: "assistant",
  content: "Hello! 👋 I'm your AI support assistant. How can I help you today?",
  timestamp: new Date().toISOString(),
};

export default function ChatWidget() {
  const { user } = useAuth();
  const [open, setOpen] = useState(false);
  const [minimised, setMinimised] = useState(false);
  const [messages, setMessages] = useState<Message[]>([WELCOME]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [unread, setUnread] = useState(0);
  const bottomRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    if (open) {
      setUnread(0);
      setMinimised(false);
      setTimeout(() => inputRef.current?.focus(), 80);
    }
  }, [open]);

  useEffect(() => {
    if (open && !minimised) {
      bottomRef.current?.scrollIntoView({ behavior: "smooth" });
    }
  }, [messages, open, minimised]);

  const sendMessage = async () => {
    if (!input.trim() || loading) return;
    const text = input.trim();
    setInput("");

    const userMsg: Message = { role: "user", content: text, timestamp: new Date().toISOString() };
    setMessages((p) => [...p, userMsg]);
    setLoading(true);

    try {
      const { data } = await chatbotApi.sendMessage(sessionId, text, user?.id);
      if (!sessionId) setSessionId(data.session_id);

      const botMsg: Message = {
        role: "assistant",
        content: data.reply ?? "Sorry, I didn't understand that.",
        timestamp: new Date().toISOString(),
      };
      setMessages((p) => [...p, botMsg]);

      // Bump unread badge if widget is closed/minimised
      if (!open || minimised) setUnread((n) => n + 1);
    } catch {
      setMessages((p) => [
        ...p,
        { role: "assistant", content: "⚠️ Sorry, there was an error. Please try again.", timestamp: new Date().toISOString() },
      ]);
    } finally {
      setLoading(false);
    }
  };

  const resetChat = () => {
    setMessages([WELCOME]);
    setSessionId(null);
    setInput("");
  };

  return (
    <div className="fixed bottom-6 right-6 z-[9999] flex flex-col items-end gap-3">
      {/* Chat panel */}
      {open && (
        <div
          className={`w-[360px] rounded-2xl shadow-2xl shadow-black/30 border border-slate-200 dark:border-white/10
            bg-white dark:bg-slate-900 flex flex-col overflow-hidden transition-all duration-300
            ${minimised ? "h-[56px]" : "h-[520px]"}`}
        >
          {/* Header */}
          <div className="flex items-center justify-between px-4 py-3 bg-indigo-600 dark:bg-indigo-700 shrink-0">
            <div className="flex items-center gap-2.5">
              <div className="w-8 h-8 rounded-full bg-white/20 flex items-center justify-center">
                <Bot className="w-4 h-4 text-white" />
              </div>
              <div>
                <p className="text-white font-semibold text-sm leading-none">Clarix AI</p>
                <p className="text-indigo-200 text-[11px] mt-0.5">Support assistant</p>
              </div>
            </div>
            <div className="flex items-center gap-1">
              <button
                onClick={resetChat}
                title="New conversation"
                className="p-1.5 rounded-lg text-white/70 hover:text-white hover:bg-white/10 transition-colors"
              >
                <RefreshCw className="w-3.5 h-3.5" />
              </button>
              <button
                onClick={() => setMinimised((v) => !v)}
                className="p-1.5 rounded-lg text-white/70 hover:text-white hover:bg-white/10 transition-colors"
              >
                <Minus className="w-3.5 h-3.5" />
              </button>
              <button
                onClick={() => setOpen(false)}
                className="p-1.5 rounded-lg text-white/70 hover:text-white hover:bg-white/10 transition-colors"
              >
                <X className="w-3.5 h-3.5" />
              </button>
            </div>
          </div>

          {/* Messages */}
          {!minimised && (
            <>
              <div className="flex-1 overflow-y-auto px-4 py-3 space-y-3">
                {messages.map((m, i) => (
                  <div key={i} className={`flex ${m.role === "user" ? "justify-end" : "justify-start"}`}>
                    {m.role === "assistant" && (
                      <div className="w-6 h-6 rounded-full bg-indigo-100 dark:bg-indigo-500/20 flex items-center justify-center shrink-0 mr-2 mt-0.5">
                        <Bot className="w-3.5 h-3.5 text-indigo-600 dark:text-indigo-400" />
                      </div>
                    )}
                    <div
                      className={`max-w-[78%] px-3.5 py-2.5 rounded-2xl text-sm leading-relaxed whitespace-pre-wrap
                        ${m.role === "user"
                          ? "bg-indigo-600 text-white rounded-br-sm"
                          : "bg-slate-100 dark:bg-white/8 text-slate-800 dark:text-white/90 rounded-bl-sm border border-slate-200 dark:border-white/5"
                        }`}
                    >
                      {m.content}
                    </div>
                  </div>
                ))}

                {loading && (
                  <div className="flex justify-start">
                    <div className="w-6 h-6 rounded-full bg-indigo-100 dark:bg-indigo-500/20 flex items-center justify-center shrink-0 mr-2">
                      <Bot className="w-3.5 h-3.5 text-indigo-600 dark:text-indigo-400" />
                    </div>
                    <div className="bg-slate-100 dark:bg-white/8 border border-slate-200 dark:border-white/5 rounded-2xl rounded-bl-sm px-4 py-3">
                      <Loader2 className="w-4 h-4 animate-spin text-indigo-500" />
                    </div>
                  </div>
                )}
                <div ref={bottomRef} />
              </div>

              {/* Input */}
              <div className="px-3 pb-3 shrink-0">
                <div className="flex items-center gap-2 bg-slate-100 dark:bg-white/5 rounded-xl border border-slate-200 dark:border-white/10 px-3 py-2">
                  <input
                    ref={inputRef}
                    value={input}
                    onChange={(e) => setInput(e.target.value)}
                    onKeyDown={(e) => e.key === "Enter" && !e.shiftKey && sendMessage()}
                    placeholder="Type a message..."
                    className="flex-1 bg-transparent text-sm text-slate-800 dark:text-white placeholder-slate-400 dark:placeholder-white/30 outline-none"
                  />
                  <button
                    onClick={sendMessage}
                    disabled={!input.trim() || loading}
                    className="p-1.5 rounded-lg bg-indigo-600 hover:bg-indigo-700 disabled:opacity-40 disabled:cursor-not-allowed text-white transition-colors"
                  >
                    <Send className="w-3.5 h-3.5" />
                  </button>
                </div>
                <p className="text-[10px] text-slate-400 dark:text-white/20 text-center mt-1.5">
                  Type "speak to agent" to reach a human
                </p>
              </div>
            </>
          )}
        </div>
      )}

      {/* FAB button */}
      <div className="relative">
        {/* Pulse ring when closed */}
        {!open && (
          <span className="absolute inset-0 rounded-full bg-indigo-500 opacity-30 animate-ping" />
        )}
        <button
          id="chat-widget-fab"
          onClick={() => setOpen((v) => !v)}
          className="relative w-14 h-14 rounded-full bg-gradient-to-br from-indigo-500 to-violet-600
            hover:from-indigo-600 hover:to-violet-700 text-white shadow-xl shadow-indigo-600/50
            flex items-center justify-center transition-all duration-200 hover:scale-110 active:scale-95"
        >
          {open
            ? <X className="w-5 h-5" />
            : <Bot className="w-7 h-7" />}
          {!open && unread > 0 && (
            <span className="absolute -top-1 -right-1 min-w-[20px] h-5 flex items-center justify-center
              bg-red-500 text-white text-[11px] font-bold rounded-full border-2 border-white dark:border-slate-900 px-1">
              {unread > 9 ? "9+" : unread}
            </span>
          )}
        </button>
      </div>
    </div>
  );
}
