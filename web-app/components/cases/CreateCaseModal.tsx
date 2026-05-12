"use client";

import { useState } from "react";
import { casesApi } from "@/lib/api";
import { useMutation } from "@tanstack/react-query";
import { X, Loader2, Bot } from "lucide-react";
import toast from "react-hot-toast";

interface Props {
  onClose: () => void;
  onCreated: () => void;
}

const CATEGORIES = ["billing","technical_support","account","shipping","returns","product_inquiry","complaint","feedback","other"];
const SOURCES = ["web","mobile","chatbot","email","phone"];

export default function CreateCaseModal({ onClose, onCreated }: Props) {
  const [form, setForm] = useState({
    title: "", message: "", source: "web", category: "", priority: "",
  });

  const { mutate, isPending } = useMutation({
    mutationFn: () => casesApi.create({
      title: form.title,
      message: form.message,
      source: form.source,
      category: form.category || undefined,
      priority: form.priority || undefined,
    }),
    onSuccess: () => {
      toast.success("Case created! AI is analysing...");
      onCreated();
    },
    onError: (e: any) => toast.error(e?.response?.data?.detail || "Failed to create case"),
  });

  return (
    <div className="fixed inset-0 bg-black/60 backdrop-blur-sm z-50 flex items-center justify-center p-4">
      <div className="bg-slate-900 border border-slate-700 rounded-2xl w-full max-w-lg shadow-2xl animate-fade-in">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b border-slate-800">
          <div>
            <h2 className="text-lg font-bold text-white">Create New Case</h2>
            <p className="text-xs text-slate-400 mt-0.5 flex items-center gap-1">
              <Bot className="w-3 h-3 text-indigo-400" />
              AI will auto-classify category, priority, and sentiment
            </p>
          </div>
          <button id="close-create-modal" onClick={onClose} className="text-slate-400 hover:text-white transition-colors p-1">
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Form */}
        <div className="p-6 space-y-4">
          <div>
            <label className="block text-sm font-medium text-slate-300 mb-1.5">Title *</label>
            <input id="case-title" className="input-field" placeholder="Brief summary of the issue"
                   value={form.title} onChange={(e) => setForm({ ...form, title: e.target.value })} />
          </div>

          <div>
            <label className="block text-sm font-medium text-slate-300 mb-1.5">Description *</label>
            <textarea id="case-message" rows={4} className="input-field resize-none"
                      placeholder="Describe the issue in detail..."
                      value={form.message} onChange={(e) => setForm({ ...form, message: e.target.value })} />
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-slate-300 mb-1.5">Category</label>
              <select id="case-category" className="input-field" value={form.category}
                      onChange={(e) => setForm({ ...form, category: e.target.value })}>
                <option value="">AI will predict</option>
                {CATEGORIES.map((c) => (
                  <option key={c} value={c}>{c.replace("_"," ")}</option>
                ))}
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium text-slate-300 mb-1.5">Priority</label>
              <select id="case-priority" className="input-field" value={form.priority}
                      onChange={(e) => setForm({ ...form, priority: e.target.value })}>
                <option value="">AI will predict</option>
                {["low","medium","high","urgent"].map((p) => (
                  <option key={p} value={p}>{p}</option>
                ))}
              </select>
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium text-slate-300 mb-1.5">Source</label>
            <select id="case-source" className="input-field" value={form.source}
                    onChange={(e) => setForm({ ...form, source: e.target.value })}>
              {SOURCES.map((s) => <option key={s} value={s}>{s}</option>)}
            </select>
          </div>
        </div>

        {/* Footer */}
        <div className="flex justify-end gap-3 px-6 pb-6">
          <button id="cancel-case" onClick={onClose} className="btn-secondary">Cancel</button>
          <button
            id="submit-case"
            onClick={() => mutate()}
            disabled={isPending || !form.title || !form.message}
            className="btn-primary"
          >
            {isPending ? <><Loader2 className="w-4 h-4 animate-spin" /> Creating...</> : "Create Case"}
          </button>
        </div>
      </div>
    </div>
  );
}
