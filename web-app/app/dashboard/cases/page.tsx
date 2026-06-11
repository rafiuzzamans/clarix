"use client";

import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { casesApi } from "@/lib/api";
import { useAuth } from "@/lib/auth-context";
import TopBar from "@/components/layout/TopBar";
import { Plus, Search, Filter, RefreshCw, ChevronLeft, ChevronRight } from "lucide-react";
import { format } from "date-fns";
import toast from "react-hot-toast";
import Link from "next/link";
import CreateCaseModal from "@/components/cases/CreateCaseModal";

const PRIORITIES = ["", "low", "medium", "high", "urgent"];
const STATUSES   = ["", "open", "in_progress", "pending_customer", "escalated", "resolved", "closed"];

export default function CasesPage() {
  const { user } = useAuth();
  const qc = useQueryClient();
  const [page, setPage] = useState(1);
  const [search, setSearch] = useState("");
  const [priority, setPriority] = useState("");
  const [status, setStatus] = useState("");
  const [showCreate, setShowCreate] = useState(false);

  const { data, isLoading, refetch } = useQuery({
    queryKey: ["cases", page, search, priority, status],
    queryFn: () =>
      casesApi
        .list({ page, page_size: 15, search: search || undefined, priority: priority || undefined, status: status || undefined })
        .then((r) => r.data),
  });

  const cases = data?.items ?? [];
  const totalPages = data?.total_pages ?? 1;

  return (
    <div className="animate-fade-in">
      <TopBar
        title="Case Management"
        subtitle={`${data?.total ?? 0} total cases`}
        actions={
          <button id="create-case-btn" onClick={() => setShowCreate(true)} className="btn-primary">
            <Plus className="w-4 h-4" />
            New Case
          </button>
        }
      />

      <div className="p-6 space-y-4">
        {/* Filters */}
        <div className="card flex flex-wrap gap-3 items-center">
          <div className="relative flex-1 min-w-48">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-500" />
            <input
              id="case-search"
              className="input-field pl-10"
              placeholder="Search cases..."
              value={search}
              onChange={(e) => { setSearch(e.target.value); setPage(1); }}
            />
          </div>
          <select id="filter-priority" className="input-field w-36" value={priority}
                  onChange={(e) => { setPriority(e.target.value); setPage(1); }}>
            {PRIORITIES.map((p) => <option key={p} value={p}>{p || "All priorities"}</option>)}
          </select>
          <select id="filter-status" className="input-field w-40" value={status}
                  onChange={(e) => { setStatus(e.target.value); setPage(1); }}>
            {STATUSES.map((s) => <option key={s} value={s}>{s ? s.replace("_"," ") : "All statuses"}</option>)}
          </select>
          <button onClick={() => refetch()} className="btn-secondary flex items-center gap-2">
            <RefreshCw className="w-4 h-4" />
          </button>
        </div>

        {/* Cases Table */}
        <div className="card p-0 overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-slate-800">
                  {["#", "Title", "Category", "Priority", "Status", "Sentiment", "Created", "Assigned"].map((h) => (
                    <th key={h} className="text-left px-4 py-3 text-xs font-semibold text-slate-400 uppercase tracking-wider whitespace-nowrap">
                      {h}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/50">
                {isLoading && (
                  <tr>
                    <td colSpan={8} className="py-12 text-center text-slate-500">Loading...</td>
                  </tr>
                )}
                {!isLoading && cases.length === 0 && (
                  <tr>
                    <td colSpan={8} className="py-12 text-center text-slate-500">No cases found</td>
                  </tr>
                )}
                {cases.map((c: any) => (
                  <tr key={c.id} className="hover:bg-slate-800/30 transition-colors">
                    <td className="px-4 py-3 text-slate-400 font-mono text-xs">#{c.case_number}</td>
                    <td className="px-4 py-3">
                      <Link href={`/dashboard/cases/${c.id}`}
                            className="text-white hover:text-indigo-300 font-medium transition-colors line-clamp-1">
                        {c.title}
                      </Link>
                      <p className="text-xs text-slate-500 mt-0.5">{c.source}</p>
                    </td>
                    <td className="px-4 py-3 text-slate-400 capitalize text-xs">{c.category?.replace("_"," ") || "—"}</td>
                    <td className="px-4 py-3"><span className={`badge-${c.priority}`}>{c.priority}</span></td>
                    <td className="px-4 py-3"><span className={`badge-${c.status}`}>{c.status?.replace("_"," ")}</span></td>
                    <td className="px-4 py-3">
                      {c.sentiment ? <span className={`badge-${c.sentiment}`}>{c.sentiment}</span> : <span className="text-slate-600">—</span>}
                    </td>
                    <td className="px-4 py-3 text-slate-400 text-xs whitespace-nowrap">
                      {format(new Date(c.created_at), "MMM d, HH:mm")}
                    </td>
                    <td className="px-4 py-3 text-slate-400 text-xs">
                      {c.assigned_to ? "Assigned" : <span className="text-orange-400">Unassigned</span>}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {/* Pagination */}
          <div className="flex items-center justify-between px-4 py-3 border-t border-slate-800">
            <span className="text-xs text-slate-500">
              Page {page} of {totalPages} · {data?.total ?? 0} records
            </span>
            <div className="flex gap-2">
              <button id="prev-page" onClick={() => setPage(Math.max(1, page - 1))} disabled={page === 1}
                      className="btn-secondary px-3 py-1.5 text-xs disabled:opacity-40">
                <ChevronLeft className="w-4 h-4" />
              </button>
              <button id="next-page" onClick={() => setPage(Math.min(totalPages, page + 1))} disabled={page === totalPages}
                      className="btn-secondary px-3 py-1.5 text-xs disabled:opacity-40">
                <ChevronRight className="w-4 h-4" />
              </button>
            </div>
          </div>
        </div>
      </div>

      {showCreate && <CreateCaseModal onClose={() => setShowCreate(false)} onCreated={() => { qc.invalidateQueries({ queryKey: ["cases"] }); setShowCreate(false); }} />}
    </div>
  );
}

# Add bulk status update

# Add export to CSV button

# Add column visibility toggle

# Highlight overdue cases in red

# Add assigned-to avatar in table

# Add empty state illustration
