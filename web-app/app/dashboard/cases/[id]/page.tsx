"use client";

import { useParams } from "next/navigation";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { casesApi, aiApi } from "@/lib/api";
import { useAuth } from "@/lib/auth-context";
import TopBar from "@/components/layout/TopBar";
import { format } from "date-fns";
import {
  AlertTriangle, Bot, Clock, MessageSquare, Send,
  ArrowUpCircle, CheckCircle, User, Paperclip, Edit2, Trash
} from "lucide-react";
import { useState } from "react";
import toast from "react-hot-toast";
import Link from "next/link";

export default function CaseDetailPage() {
  const { id } = useParams<{ id: string }>();
  const { user } = useAuth();
  const qc = useQueryClient();
  const [note, setNote] = useState("");
  const [isInternal, setIsInternal] = useState(true);
  const [escalateReason, setEscalateReason] = useState("");
  const [showEscalate, setShowEscalate] = useState(false);
  const [editingNoteId, setEditingNoteId] = useState<string | null>(null);
  const [editNoteContent, setEditNoteContent] = useState("");

  const { data: caseData, isLoading } = useQuery({
    queryKey: ["case", id],
    queryFn: () => casesApi.get(id).then((r) => r.data),
  });

  const { data: notes = [] } = useQuery({
    queryKey: ["case-notes", id],
    queryFn: () => casesApi.getNotes(id).then((r) => r.data),
  });

  const { data: timeline = [] } = useQuery({
    queryKey: ["case-timeline", id],
    queryFn: () => casesApi.getTimeline(id).then((r) => r.data),
  });

  const addNoteMutation = useMutation({
    mutationFn: () => casesApi.addNote(id, note, isInternal),
    onSuccess: () => {
      setNote("");
      qc.invalidateQueries({ queryKey: ["case-notes", id] });
      toast.success("Note added");
    },
  });

  const editNoteMutation = useMutation({
    mutationFn: ({ noteId, content }: { noteId: string, content: string }) => casesApi.editNote(id, noteId, content),
    onSuccess: () => {
      setEditingNoteId(null);
      setEditNoteContent("");
      qc.invalidateQueries({ queryKey: ["case-notes", id] });
      toast.success("Note updated");
    },
  });

  const deleteNoteMutation = useMutation({
    mutationFn: (noteId: string) => casesApi.deleteNote(id, noteId),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["case-notes", id] });
      toast.success("Note deleted");
    },
  });

  const updateStatusMutation = useMutation({
    mutationFn: (status: string) => casesApi.update(id, { status }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["case", id] }),
  });

  const escalateMutation = useMutation({
    mutationFn: () => casesApi.escalate(id, escalateReason),
    onSuccess: () => {
      setShowEscalate(false);
      setEscalateReason("");
      qc.invalidateQueries({ queryKey: ["case", id] });
      toast.success("Case escalated");
    },
  });

  const generateReplyMutation = useMutation({
    mutationFn: () => aiApi.generateReply(
      caseData?.message || "",
      caseData?.ai_category || caseData?.category || "general",
      caseData?.ai_sentiment || caseData?.sentiment || "neutral",
      caseData?.ai_priority || caseData?.priority || "medium"
    ).then((r) => r.data),
    onSuccess: (data) => {
      setNote(data.generated_reply);
      setIsInternal(false);
      toast.success("AI reply generated!");
    },
    onError: () => {
      toast.error("Failed to generate AI reply.");
    }
  });

  if (isLoading) {
    return <div className="p-6 text-slate-400">Loading case...</div>;
  }

  const c = caseData;
  const canEdit = user?.role !== "customer";

  return (
    <div className="animate-fade-in">
      <TopBar
        title={`Case #${c?.case_number}`}
        subtitle={c?.title}
        actions={
          <Link href="/dashboard/cases" className="btn-secondary text-sm">← Back</Link>
        }
      />

      <div className="p-6 grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Main column */}
        <div className="lg:col-span-2 space-y-6">

          {/* Case content */}
          <div className="card">
            <h3 className="text-base font-semibold text-slate-900 dark:text-white mb-3">Description</h3>
            <p className="text-slate-700 dark:text-slate-300 text-sm leading-relaxed whitespace-pre-wrap">{c?.message}</p>
          </div>

          {/* AI Predictions */}
          {(c?.ai_category || c?.ai_priority || c?.ai_sentiment) && (
            <div className="card border-indigo-200 dark:border-indigo-500/30 bg-indigo-50/50 dark:bg-indigo-950/20">
              <div className="flex items-center gap-2 mb-3">
                <Bot className="w-5 h-5 text-indigo-600 dark:text-indigo-400" />
                <h3 className="text-base font-semibold text-indigo-800 dark:text-indigo-300">AI Analysis</h3>
                <span className="text-xs text-slate-500">Confidence: {Math.round((c.ai_confidence || 0) * 100)}%</span>
              </div>
              <div className="grid grid-cols-3 gap-4">
                {[
                  { label: "Category",  value: c.ai_category?.replace("_"," ") },
                  { label: "Priority",  value: c.ai_priority },
                  { label: "Sentiment", value: c.ai_sentiment },
                ].map(({ label, value }) => (
                  <div key={label} className="bg-white/60 dark:bg-indigo-900/20 rounded-xl p-3 border border-indigo-200 dark:border-indigo-800/30">
                    <p className="text-xs text-slate-500 mb-1">{label}</p>
                    <p className="text-sm font-semibold text-slate-900 dark:text-white capitalize">{value || "—"}</p>
                  </div>
                ))}
              </div>

              {c.ai_explanation && (() => {
                const parsedAiExp = typeof c.ai_explanation === "string" ? JSON.parse(c.ai_explanation) : c.ai_explanation;
                const topFeatures = Array.isArray(parsedAiExp) ? parsedAiExp : (parsedAiExp?.top_features || []);
                const probabilities = Array.isArray(parsedAiExp) ? null : (parsedAiExp?.probabilities || null);
                
                return (
                  <div className="mt-4 pt-4 border-t border-indigo-200 dark:border-indigo-800/30 grid grid-cols-1 md:grid-cols-2 gap-6">
                    
                    {probabilities && (
                      <div>
                        <h4 className="text-xs font-semibold text-slate-500 mb-2 uppercase tracking-wider">Confidence Breakdown</h4>
                        <div className="space-y-2">
                          {Object.entries(probabilities)
                            .sort((a: any, b: any) => b[1] - a[1])
                            .slice(0, 3)
                            .map(([cat, prob]: any) => (
                              <div key={cat} className="flex items-center gap-2 text-xs">
                                <span className="w-28 truncate text-slate-600 dark:text-slate-400 capitalize">{cat.replace("_", " ")}</span>
                                <div className="flex-1 h-1.5 bg-slate-200 dark:bg-slate-700 rounded-full overflow-hidden">
                                  <div className="h-full bg-indigo-500 rounded-full" style={{ width: `${Math.max(prob * 100, 1)}%` }}></div>
                                </div>
                                <span className="w-10 text-right text-slate-600 dark:text-slate-400">{(prob * 100).toFixed(1)}%</span>
                              </div>
                            ))}
                        </div>
                      </div>
                    )}
                    
                    {topFeatures.length > 0 && (
                      <div>
                        <h4 className="text-xs font-semibold text-slate-500 mb-2 uppercase tracking-wider">Top AI Features</h4>
                        <div className="flex flex-wrap gap-2">
                          {topFeatures.slice(0, 5).map((feat: any, idx: number) => (
                            <span key={idx} className="px-2 py-1 bg-white dark:bg-slate-800 border border-indigo-100 dark:border-indigo-800 rounded-md text-xs text-slate-600 dark:text-slate-300">
                              {feat.feature} <span className={feat.direction === "positive" ? "text-emerald-500" : "text-rose-500"}>({feat.shap_value.toFixed(2)})</span>
                            </span>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>
                );
              })()}
            </div>
          )}

          {/* Notes */}
          <div className="card">
            <h3 className="text-base font-semibold text-slate-900 dark:text-white mb-4 flex items-center gap-2">
              <MessageSquare className="w-4 h-4 text-slate-500 dark:text-slate-400" />
              Notes ({notes.length})
            </h3>

            <div className="space-y-3 mb-4 max-h-64 overflow-y-auto">
              {notes.map((n: any) => (
                <div key={n.id} className={`p-3 rounded-xl text-sm relative group ${
                  n.is_internal
                    ? "bg-yellow-50 dark:bg-yellow-950/30 border border-yellow-200 dark:border-yellow-800/30"
                    : "bg-slate-50 dark:bg-slate-800/50 border border-slate-200 dark:border-slate-700/50"
                }`}>
                  <div className="flex items-center gap-2 mb-1 justify-between">
                    <div className="flex items-center gap-2">
                      <span className="text-xs text-slate-500">
                        {n.is_internal
                          ? "🔒 Internal note"
                          : "💬 Public reply"}
                      </span>
                      <span className="text-xs text-slate-600">·</span>
                      <span className="text-xs text-slate-500">
                        {format(new Date(n.created_at), "MMM d, HH:mm")}
                      </span>
                    </div>
                    {/* Action buttons (only show if author is current user or user is admin, for simplicity we allow if canEdit) */}
                    {canEdit && (
                      <div className="flex gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
                        <button 
                          onClick={() => { setEditingNoteId(n.id); setEditNoteContent(n.content); }}
                          className="p-1 text-slate-400 hover:text-indigo-500 transition-colors"
                          title="Edit Note"
                        >
                          <Edit2 className="w-3.5 h-3.5" />
                        </button>
                        <button 
                          onClick={() => { if(confirm("Delete this note?")) deleteNoteMutation.mutate(n.id); }}
                          className="p-1 text-slate-400 hover:text-rose-500 transition-colors"
                          title="Delete Note"
                        >
                          <Trash className="w-3.5 h-3.5" />
                        </button>
                      </div>
                    )}
                  </div>
                  
                  {editingNoteId === n.id ? (
                    <div className="mt-2 space-y-2">
                      <textarea
                        className="input-field w-full text-sm"
                        rows={3}
                        value={editNoteContent}
                        onChange={(e) => setEditNoteContent(e.target.value)}
                        autoFocus
                      />
                      <div className="flex justify-end gap-2">
                        <button 
                          onClick={() => setEditingNoteId(null)}
                          className="px-2 py-1 text-xs text-slate-500 hover:text-slate-700 dark:hover:text-slate-300"
                        >
                          Cancel
                        </button>
                        <button 
                          onClick={() => editNoteMutation.mutate({ noteId: n.id, content: editNoteContent })}
                          disabled={editNoteMutation.isPending || !editNoteContent.trim()}
                          className="btn-primary px-3 py-1 text-xs"
                        >
                          {editNoteMutation.isPending ? "Saving..." : "Save"}
                        </button>
                      </div>
                    </div>
                  ) : (
                    <p className="text-slate-700 dark:text-slate-300 whitespace-pre-wrap mt-1">{n.content}</p>
                  )}
                </div>
              ))}
              {notes.length === 0 && (
                <p className="text-slate-500 text-sm text-center py-4">No notes yet</p>
              )}
            </div>

            {canEdit && (
              <div className="space-y-2">
                <div className="flex gap-2 text-xs">
                  <button
                    onClick={() => setIsInternal(true)}
                    className={`px-3 py-1.5 rounded-lg transition-colors ${isInternal ? "bg-yellow-900/40 text-yellow-300 border border-yellow-700/50" : "bg-slate-800 text-slate-400"}`}
                  >
                    🔒 Internal
                  </button>
                  <button
                    onClick={() => setIsInternal(false)}
                    className={`px-3 py-1.5 rounded-lg transition-colors ${!isInternal ? "bg-indigo-900/40 text-indigo-300 border border-indigo-700/50" : "bg-slate-800 text-slate-400"}`}
                  >
                    💬 Public
                  </button>
                  <button
                    onClick={() => generateReplyMutation.mutate()}
                    disabled={generateReplyMutation.isPending}
                    className="ml-auto px-3 py-1.5 rounded-lg transition-colors bg-purple-900/40 text-purple-300 border border-purple-700/50 hover:bg-purple-800/60 disabled:opacity-50"
                  >
                    {generateReplyMutation.isPending ? "Generating..." : "✨ Generate AI Reply"}
                  </button>
                </div>
                <div className="flex gap-2">
                  <textarea
                    id="note-input"
                    rows={5}
                    className="input-field flex-1 text-sm"
                    placeholder="Add a note..."
                    value={note}
                    onChange={(e) => setNote(e.target.value)}
                  />
                  <button
                    id="add-note-btn"
                    onClick={() => addNoteMutation.mutate()}
                    disabled={!note.trim() || addNoteMutation.isPending}
                    className="btn-primary px-4"
                  >
                    <Send className="w-4 h-4" />
                  </button>
                </div>
              </div>
            )}
          </div>

          {/* Timeline */}
          <div className="card">
            <h3 className="text-base font-semibold text-slate-900 dark:text-white mb-4 flex items-center gap-2">
              <Clock className="w-4 h-4 text-slate-500 dark:text-slate-400" />
              Timeline
            </h3>
            <div className="space-y-3 relative before:absolute before:left-3.5 before:top-0 before:bottom-0 before:border-l before:border-slate-200 dark:before:border-slate-700">
              {timeline.map((t: any) => (
                <div key={t.id} className="flex gap-3 pl-8 relative">
                  <div className="absolute left-2.5 top-1.5 w-2 h-2 rounded-full bg-indigo-500 shrink-0" />
                  <div>
                    <p className="text-sm text-slate-700 dark:text-slate-300">{t.description}</p>
                    <p className="text-xs text-slate-500 mt-0.5">
                      {format(new Date(t.created_at), "MMM d, yyyy HH:mm")}
                    </p>
                  </div>
                </div>
              ))}
              {timeline.length === 0 && (
                <p className="text-slate-500 text-sm">No timeline entries</p>
              )}
            </div>
          </div>
        </div>

        {/* Sidebar column */}
        <div className="space-y-4">
          {/* Status & Actions */}
          <div className="card">
            <h3 className="text-sm font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wider mb-4">Case Details</h3>
            <div className="space-y-3 text-sm">
              {[
                { label: "Status",   value: <span className={`badge-${c?.status}`}>{c?.status?.replace("_"," ")}</span> },
                { label: "Priority", value: <span className={`badge-${c?.priority}`}>{c?.priority}</span> },
                { label: "Sentiment",value: c?.sentiment ? <span className={`badge-${c?.sentiment}`}>{c?.sentiment}</span> : "—" },
                { label: "Source",   value: <span className="capitalize text-slate-900 dark:text-slate-300">{c?.source}</span> },
                { label: "Category", value: <span className="text-slate-900 dark:text-slate-300 capitalize">{c?.category?.replace("_"," ") || "—"}</span> },
                { label: "SLA",      value: c?.sla_deadline ? (
                  <span className={new Date(c.sla_deadline) < new Date() ? "text-red-400" : "text-emerald-400"}>
                    {format(new Date(c.sla_deadline), "MMM d, HH:mm")}
                  </span>
                ) : "—" },
                { label: "Created",  value: <span className="text-slate-500 dark:text-slate-400">{c?.created_at ? format(new Date(c.created_at), "MMM d, HH:mm"): "—"}</span> },
              ].map(({ label, value }) => (
                <div key={label} className="flex items-center justify-between gap-2">
                  <span className="text-slate-500">{label}</span>
                  <span className="text-slate-900 dark:text-slate-300">{value}</span>
                </div>
              ))}
            </div>
          </div>

          {/* Actions */}
          {canEdit && (
            <div className="card space-y-2">
              <h3 className="text-sm font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wider mb-2">Actions</h3>

              {c?.status !== "resolved" && (
                <button
                  id="resolve-btn"
                  onClick={() => updateStatusMutation.mutate("resolved")}
                  className="btn-primary w-full justify-center"
                >
                  <CheckCircle className="w-4 h-4" /> Mark Resolved
                </button>
              )}

              {!c?.is_escalated && (
                <button
                  id="escalate-btn"
                  onClick={() => setShowEscalate(!showEscalate)}
                  className="w-full flex items-center justify-center gap-2 px-4 py-2.5 rounded-xl
                             bg-orange-600/20 hover:bg-orange-600/30 text-orange-400
                             border border-orange-500/30 text-sm font-medium transition-all"
                >
                  <AlertTriangle className="w-4 h-4" /> Escalate Case
                </button>
              )}

              {showEscalate && (
                <div className="space-y-2 animate-fade-in">
                  <textarea
                    className="input-field text-sm resize-none"
                    rows={2}
                    placeholder="Reason for escalation..."
                    value={escalateReason}
                    onChange={(e) => setEscalateReason(e.target.value)}
                  />
                  <button
                    onClick={() => escalateMutation.mutate()}
                    disabled={!escalateReason.trim()}
                    className="btn-danger w-full justify-center flex items-center gap-2"
                  >
                    Confirm Escalation
                  </button>
                </div>
              )}

              <button
                onClick={() => updateStatusMutation.mutate("closed")}
                className="btn-secondary w-full justify-center flex items-center gap-2 text-sm"
              >
                Close Case
              </button>
            </div>
          )}

          {/* Escalated badge */}
          {c?.is_escalated && (
            <div className="card border-red-500/30 bg-red-950/20">
              <div className="flex items-center gap-2 text-red-400">
                <AlertTriangle className="w-4 h-4" />
                <span className="text-sm font-semibold">Case is Escalated</span>
              </div>
              {c?.escalation_reason && (
                <p className="text-xs text-red-300/70 mt-2">{c.escalation_reason}</p>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
