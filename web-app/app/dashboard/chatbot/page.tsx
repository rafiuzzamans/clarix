"use client";

import { useState, useRef, useEffect } from "react";
import { chatbotApi } from "@/lib/api";
import { useAuth } from "@/lib/auth-context";
import TopBar from "@/components/layout/TopBar";
import { Bot, Send, Loader2, User, AlertTriangle, Ticket, RefreshCw } from "lucide-react";
import { format } from "date-fns";

interface Message {
  role: "user" | "assistant" | "system";
  content: string;
  timestamp: string;
  intent?: string;
  action?: string;
  case_id?: string;
}

export default function ChatbotPage() {
  const { user } = useAuth();
  const [messages, setMessages] = useState<Message[]>([
    {
      role: "assistant",
      content: "Hello! Welcome to Customer Support 👋\n\nI can help you with orders, billing, account issues, and more. How can I help you today?",
      timestamp: new Date().toISOString(),
    },
  ]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [state, setState] = useState("idle");
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const sendMessage = async () => {
    if (!input.trim() || loading) return;
    const text = input.trim();
    setInput("");

    const userMsg: Message = {
      role: "user",
      content: text,
      timestamp: new Date().toISOString(),
    };
    setMessages((prev) => [...prev, userMsg]);
    setLoading(true);

    try {
      const { data } = await chatbotApi.sendMessage(sessionId, text, user?.id);
      if (!sessionId) setSessionId(data.session_id);
      setState(data.state);

      const botMsg: Message = {
        role: "assistant",
        content: data.reply,
        timestamp: new Date().toISOString(),
        intent: data.intent,
        action: data.action,
        case_id: data.case_id,
      };

      // Show system action messages
      if (data.action === "create_case" && data.case_id) {
        const sysMsg: Message = {
          role: "system",
          content: `✅ Support ticket created — Case ID: ${data.case_id}`,
          timestamp: new Date().toISOString(),
          case_id: data.case_id,
        };
        setMessages((prev) => [...prev, botMsg, sysMsg]);
      } else if (data.action === "escalate") {
        const sysMsg: Message = {
          role: "system",
          content: "🚨 Escalating to human agent — a ticket has been raised.",
          timestamp: new Date().toISOString(),
        };
        setMessages((prev) => [...prev, botMsg, sysMsg]);
      } else {
        setMessages((prev) => [...prev, botMsg]);
      }
    } catch {
      setMessages((prev) => [...prev, {
        role: "system",
        content: "⚠️ Sorry, there was an error. Please try again.",
        timestamp: new Date().toISOString(),
      }]);
    } finally {
      setLoading(false);
    }
  };

  const resetChat = () => {
    setMessages([{
      role: "assistant",
      content: "Hello! Welcome to Customer Support 👋 How can I help you today?",
      timestamp: new Date().toISOString(),
    }]);
    setSessionId(null);
    setState("idle");
    setInput("");
  };

  const suggestions = [
    "Reset my password",
    "Track my order",
    "Request a refund",
    "Speak to an agent",
  ];

  return (
    <div className="animate-fade-in flex flex-col h-screen">
      <TopBar
        title="Customer Chatbot"
        subtitle="AI-powered support assistant"
        actions={
          <button onClick={resetChat} className="btn-secondary flex items-center gap-2 text-sm">
            <RefreshCw className="w-4 h-4" /> New Session
          </button>
        }
      />

      <div className="flex flex-1 overflow-hidden p-6 gap-6">
        {/* Chat window */}
        <div className="flex-1 flex flex-col card p-0 overflow-hidden">
          {/* Status bar */}
          <div className="flex items-center gap-3 px-4 py-3 border-b border-slate-800 bg-slate-900/50">
            <div className="flex items-center gap-2">
              <div className={`w-2 h-2 rounded-full ${state === "escalated" ? "bg-red-500" : state === "resolved" ? "bg-emerald-500" : "bg-green-400 animate-pulse"}`} />
              <span className="text-xs text-slate-400 capitalize">
                {state === "idle" ? "Connected" : state}
              </span>
            </div>
            {sessionId && (
              <span className="text-xs text-slate-600 font-mono ml-auto">
                Session: {sessionId.slice(0, 8)}...
              </span>
            )}
          </div>

          {/* Messages */}
          <div className="flex-1 overflow-y-auto p-4 space-y-4">
            {messages.map((msg, i) => (
              <div key={i} className={`flex gap-3 ${msg.role === "user" ? "flex-row-reverse" : "flex-row"}`}>
                {/* Avatar */}
                <div className={`w-8 h-8 rounded-full flex items-center justify-center shrink-0 ${
                  msg.role === "user" ? "bg-gradient-to-br from-indigo-500 to-violet-600" :
                  msg.role === "system" ? "bg-slate-700" :
                  "bg-gradient-to-br from-emerald-500 to-teal-600"
                }`}>
                  {msg.role === "user" ? (
                    <User className="w-4 h-4 text-white" />
                  ) : msg.role === "system" ? (
                    <Ticket className="w-4 h-4 text-slate-300" />
                  ) : (
                    <Bot className="w-4 h-4 text-white" />
                  )}
                </div>

                {/* Bubble */}
                <div className={`max-w-[75%] ${msg.role === "user" ? "items-end" : "items-start"} flex flex-col gap-1`}>
                  <div className={`px-4 py-3 rounded-2xl text-sm leading-relaxed whitespace-pre-wrap ${
                    msg.role === "user"
                      ? "bg-indigo-600 text-white rounded-tr-none"
                      : msg.role === "system"
                      ? "bg-slate-800 text-slate-300 border border-slate-700 rounded-tl-none text-xs"
                      : "bg-slate-800 text-slate-200 rounded-tl-none"
                  }`}>
                    {msg.content}
                    {msg.case_id && (
                      <a href={`/dashboard/cases/${msg.case_id}`}
                         className="block mt-2 text-xs text-indigo-400 hover:text-indigo-300 underline">
                        View Case →
                      </a>
                    )}
                  </div>
                  <span className="text-xs text-slate-600 px-1">
                    {format(new Date(msg.timestamp), "HH:mm")}
                    {msg.intent && <span className="ml-2 text-indigo-500/60">· {msg.intent}</span>}
                  </span>
                </div>
              </div>
            ))}

            {loading && (
              <div className="flex gap-3">
                <div className="w-8 h-8 rounded-full bg-gradient-to-br from-emerald-500 to-teal-600 flex items-center justify-center">
                  <Bot className="w-4 h-4 text-white" />
                </div>
                <div className="bg-slate-800 rounded-2xl rounded-tl-none px-4 py-3 flex items-center gap-2">
                  <Loader2 className="w-4 h-4 text-slate-400 animate-spin" />
                  <span className="text-sm text-slate-400">Typing...</span>
                </div>
              </div>
            )}
            <div ref={bottomRef} />
          </div>

          {/* Quick suggestions */}
          {messages.length === 1 && (
            <div className="px-4 pb-3 flex flex-wrap gap-2">
              {suggestions.map((s) => (
                <button
                  key={s}
                  onClick={() => { setInput(s); }}
                  className="text-xs px-3 py-1.5 bg-slate-800 hover:bg-slate-700 text-slate-300
                             border border-slate-700 rounded-lg transition-all"
                >
                  {s}
                </button>
              ))}
            </div>
          )}

          {/* Input */}
          <div className="p-4 border-t border-slate-800">
            <div className="flex gap-3">
              <input
                id="chatbot-input"
                type="text"
                className="input-field flex-1"
                placeholder="Type your message..."
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyDown={(e) => e.key === "Enter" && !e.shiftKey && sendMessage()}
                disabled={state === "escalated" || state === "resolved"}
              />
              <button
                id="chatbot-send"
                onClick={sendMessage}
                disabled={!input.trim() || loading || state === "escalated" || state === "resolved"}
                className="btn-primary px-4"
              >
                <Send className="w-4 h-4" />
              </button>
            </div>
            {(state === "escalated" || state === "resolved") && (
              <p className="text-xs text-slate-500 mt-2 text-center">
                Session ended. <button onClick={resetChat} className="text-indigo-400 hover:text-indigo-300">Start new session</button>
              </p>
            )}
          </div>
        </div>

        {/* Info sidebar */}
        <div className="w-72 space-y-4 hidden lg:flex lg:flex-col">
          <div className="card">
            <h3 className="text-sm font-semibold text-white mb-3 flex items-center gap-2">
              <Bot className="w-4 h-4 text-indigo-400" /> How I can help
            </h3>
            <ul className="space-y-2 text-xs text-slate-400">
              {[
                "Answer frequently asked questions",
                "Help track orders and deliveries",
                "Assist with billing and refunds",
                "Create support tickets automatically",
                "Connect you with a human agent",
                "Provide account and password help",
              ].map((item) => (
                <li key={item} className="flex items-start gap-2">
                  <span className="text-emerald-400 mt-0.5">✓</span>
                  {item}
                </li>
              ))}
            </ul>
          </div>

          <div className="card border-orange-500/20 bg-orange-950/10">
            <div className="flex items-center gap-2 mb-2">
              <AlertTriangle className="w-4 h-4 text-orange-400" />
              <h3 className="text-sm font-semibold text-orange-300">Emergency?</h3>
            </div>
            <p className="text-xs text-slate-400">
              Type <code className="text-orange-400">"speak to agent"</code> or <code className="text-orange-400">"escalate"</code> at any time to connect with a human.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
