"use client";

import { useQuery } from "@tanstack/react-query";
import { auditApi, aiApi } from "@/lib/api";
import TopBar from "@/components/layout/TopBar";
import { format } from "date-fns";
import { Shield, Bot, RefreshCw } from "lucide-react";
import { useState } from "react";

export default function AuditPage() {
  const [action, setAction] = useState("");
  const { data, refetch, isLoading } = useQuery({
    queryKey: ["audit-logs", action],
    queryFn: () => auditApi.logs({ action: action||undefined, limit: 100 }).then(r=>r.data),
  });

  const { data: aiStatus } = useQuery({
    queryKey: ["ai-status"],
    queryFn: () => aiApi.status().then(r=>r.data),
  });

  const logs = data?.logs ?? [];

  const actionColors: Record<string, string> = {
    login: "text-emerald-400", logout: "text-slate-400",
    login_failed: "text-red-400", token_refresh: "text-blue-400",
    case_created: "text-indigo-400", case_escalated: "text-orange-400",
    ai_prediction: "text-violet-400", ai_override: "text-yellow-400",
    user_created: "text-cyan-400", user_deactivated: "text-red-400",
  };

  return (
    <div className="animate-fade-in">
      <TopBar title="Audit Logs" subtitle="Full activity trail for the platform" />

      <div className="p-6 space-y-6">
        {/* AI Status Card */}
        {aiStatus && (
          <div className="card border-violet-500/30 bg-violet-950/10">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                <Bot className="w-5 h-5 text-violet-400" />
                <div>
                  <p className="text-sm font-semibold text-white">AI Model Status</p>
                  <p className="text-xs text-slate-400">
                    Models loaded: {aiStatus.models_available?.join(", ") || "none"}
                  </p>
                </div>
              </div>
              <div className={`px-3 py-1.5 rounded-xl text-xs font-semibold ${aiStatus.models_loaded ? "bg-emerald-900/40 text-emerald-300" : "bg-red-900/40 text-red-300"}`}>
                {aiStatus.models_loaded ? "Ready" : "Not trained"}
              </div>
            </div>
            {aiStatus.evaluation_report && (
              <div className="mt-4 grid grid-cols-3 gap-3">
                {Object.entries(aiStatus.evaluation_report).map(([model, metrics]: any) => (
                  <div key={model} className="bg-slate-800/50 rounded-xl p-3 border border-slate-700/50">
                    <p className="text-xs text-slate-400 capitalize mb-2">{model} model</p>
                    <p className="text-sm font-bold text-white">
                      Acc: {(metrics.accuracy * 100).toFixed(1)}%
                    </p>
                    <p className="text-xs text-violet-400">
                      F1: {(metrics.f1_weighted * 100).toFixed(1)}%
                    </p>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}

        {/* Filters */}
        <div className="card flex flex-wrap gap-3 items-center">
          <Shield className="w-4 h-4 text-slate-400" />
          <span className="text-sm text-slate-400">Filter by action:</span>
          <input className="input-field w-56" placeholder="e.g. login, case_created..."
                 value={action} onChange={e=>setAction(e.target.value)} />
          <button onClick={()=>refetch()} className="btn-secondary"><RefreshCw className="w-4 h-4"/></button>
          <span className="text-xs text-slate-500 ml-auto">{data?.total ?? 0} total entries</span>
        </div>

        {/* Logs table */}
        <div className="card p-0 overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-slate-800">
                  {["Timestamp","Action","Actor","Resource","Description","IP"].map(h=>(
                    <th key={h} className="text-left px-4 py-3 text-xs font-semibold text-slate-400 uppercase tracking-wider whitespace-nowrap">{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/50">
                {isLoading && <tr><td colSpan={6} className="py-8 text-center text-slate-500">Loading...</td></tr>}
                {logs.map((l: any) => (
                  <tr key={l.log_id} className="hover:bg-slate-800/20 transition-colors">
                    <td className="px-4 py-2.5 text-slate-500 text-xs font-mono whitespace-nowrap">
                      {format(new Date(l.timestamp), "MMM d HH:mm:ss")}
                    </td>
                    <td className="px-4 py-2.5">
                      <span className={`text-xs font-semibold font-mono ${actionColors[l.action] || "text-slate-300"}`}>
                        {l.action}
                      </span>
                    </td>
                    <td className="px-4 py-2.5 text-slate-400 text-xs font-mono">
                      {l.actor_id === "99999999-9999-9999-9999-999999999999" ? (
                        <span className="text-indigo-400 font-semibold tracking-wider">AI AGENT</span>
                      ) : (
                        l.actor_id?.slice(0,8) || "system"
                      )}
                    </td>
                    <td className="px-4 py-2.5 text-xs text-slate-500">
                      {l.resource_type && <span className="capitalize">{l.resource_type}</span>}
                      {l.resource_id && <span className="font-mono ml-1 text-slate-600">·{l.resource_id.slice(0,8)}</span>}
                    </td>
                    <td className="px-4 py-2.5 text-slate-300 text-xs max-w-xs truncate">{l.description}</td>
                    <td className="px-4 py-2.5 text-slate-500 text-xs font-mono">{l.ip_address || "—"}</td>
                  </tr>
                ))}
                {!isLoading && logs.length === 0 && (
                  <tr><td colSpan={6} className="py-8 text-center text-slate-500">No log entries</td></tr>
                )}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>
  );
}
