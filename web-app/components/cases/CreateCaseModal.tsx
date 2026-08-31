"use client";

import { useState } from "react";
import { X, Loader2, Bot } from "lucide-react";
import { casesApi } from "@/lib/api";
import toast from "react-hot-toast";

interface Props {
  onClose: () => void;
  onCreated: () => void;
}

export default function CreateCaseModal({ onClose, onCreated }: Props) {
  const [loading, setLoading] = useState(false);
  const [form, setForm] = useState({
    title: "",
    message: "",
    source: "web"
  });

  const isFormValid = form.title.trim().length > 0 && form.message.trim().length > 0;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!isFormValid) return;
    
    setLoading(true);
    try {
      await casesApi.create({
        title: form.title,
        message: form.message,
        source: form.source
      });
      toast.success("Case created successfully!");
      onCreated();
    } catch (error: any) {
      const detail = error.response?.data?.detail;
      const msg = Array.isArray(detail) ? detail[0].msg : detail || "Failed to create case";
      toast.error(msg);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 bg-slate-900/40 dark:bg-black/60 flex items-center justify-center p-4 backdrop-blur-sm animate-fade-in">
      <div className="card w-full max-w-md animate-slide-in relative overflow-hidden shadow-2xl border border-slate-200 dark:border-white/10">
        <button onClick={onClose} className="absolute right-4 top-4 p-2 rounded-lg text-slate-400 hover:text-slate-600 hover:bg-slate-100 dark:hover:text-white dark:hover:bg-white/10 transition-all">
          <X className="w-5 h-5" />
        </button>
        
        <h2 className="text-xl font-bold text-slate-900 dark:text-white mb-6">Create New Case</h2>
        
        <form onSubmit={handleSubmit} className="space-y-5">
          <div>
            <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1.5">Title</label>
            <input 
              required 
              type="text" 
              className="input-field" 
              value={form.title} 
              onChange={e => setForm({...form, title: e.target.value})} 
              placeholder="Brief summary..." 
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1.5">Message</label>
            <textarea 
              required 
              className="input-field resize-none h-24" 
              value={form.message} 
              onChange={e => setForm({...form, message: e.target.value})} 
              placeholder="Describe the issue..." 
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1.5">Source</label>
            <select className="input-field" value={form.source} onChange={e => setForm({...form, source: e.target.value})}>
              <option value="web">web</option>
              <option value="email">email</option>
              <option value="phone">phone</option>
              <option value="chat">chat</option>
            </select>
          </div>

          <div className="bg-indigo-50 dark:bg-indigo-900/20 p-3 rounded-lg flex items-center gap-2 border border-indigo-100 dark:border-indigo-800/30">
            <Bot className="w-4 h-4 text-indigo-600 dark:text-indigo-400 shrink-0" />
            <p className="text-xs text-indigo-800 dark:text-indigo-300">
              AI will auto-classify and route this case based on the description.
            </p>
          </div>

          <div className="pt-2 flex gap-3 justify-end">
            <button type="button" onClick={onClose} className="btn-secondary">Cancel</button>
            <button type="submit" disabled={!isFormValid || loading} className="btn-primary min-w-[120px]">
              {loading ? <Loader2 className="w-5 h-5 animate-spin mx-auto" /> : "Create Case"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
