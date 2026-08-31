"use client";

import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { usersApi } from "@/lib/api";
import TopBar from "@/components/layout/TopBar";
import { Plus, Search, RefreshCw, ShieldCheck, UserX, UserCheck, Edit2, Trash2 } from "lucide-react";
import { format } from "date-fns";
import toast from "react-hot-toast";
import CreateUserModal from "../../../components/users/CreateUserModal";
import EditUserModal from "../../../components/users/EditUserModal";

const ROLES = ["","customer","agent","supervisor","manager","admin"];
const STATUSES = ["","active","inactive","suspended"];

export default function UsersPage() {
  const qc = useQueryClient();
  const [search, setSearch] = useState("");
  const [role, setRole] = useState("");
  const [status, setStatus] = useState("");
  const [page, setPage] = useState(1);
  const [showCreate, setShowCreate] = useState(false);
  const [editingUser, setEditingUser] = useState<any>(null);

  const { data, isLoading, refetch } = useQuery({
    queryKey: ["users", page, search, role, status],
    queryFn: () =>
      usersApi.list({ page, page_size: 20, search: search||undefined, role: role||undefined, status: status||undefined })
        .then(r => r.data),
  });

  const users = data?.items ?? [];

  const deactivate = useMutation({
    mutationFn: (id: string) => usersApi.deactivate(id),
    onSuccess: () => { qc.invalidateQueries({ queryKey: ["users"] }); toast.success("User deactivated"); },
    onError: (error: any) => toast.error(error.response?.data?.detail || "Failed to deactivate user"),
  });

  const hardDelete = useMutation({
    mutationFn: (id: string) => usersApi.hardDelete(id),
    onSuccess: () => { qc.invalidateQueries({ queryKey: ["users"] }); toast.success("User permanently deleted"); },
    onError: (error: any) => toast.error(error.response?.data?.detail || "Failed to delete user"),
  });

  const activate = useMutation({
    mutationFn: (id: string) => usersApi.updateStatus(id, "active"),
    onSuccess: () => { qc.invalidateQueries({ queryKey: ["users"] }); toast.success("User activated"); },
    onError: (error: any) => toast.error(error.response?.data?.detail || "Failed to activate user"),
  });

  return (
    <div className="animate-fade-in">
      <TopBar 
        title="User Management" 
        subtitle={`${data?.total ?? 0} total users`} 
        actions={
          <button id="create-user-btn" onClick={() => setShowCreate(true)} className="btn-primary">
            <Plus className="w-4 h-4" />
            New User
          </button>
        }
      />

      <div className="p-6 space-y-4">
        {/* Filters */}
        <div className="card flex flex-wrap gap-3 items-center">
          <div className="relative flex-1 min-w-48">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-500" />
            <input id="user-search" className="input-field pl-10" placeholder="Search by name or email..."
                   value={search} onChange={(e) => { setSearch(e.target.value); setPage(1); }} />
          </div>
          <select id="filter-role" className="input-field w-36" value={role}
                  onChange={(e) => { setRole(e.target.value); setPage(1); }}>
            {ROLES.map(r => <option key={r} value={r}>{r || "All roles"}</option>)}
          </select>
          <select id="filter-status" className="input-field w-36" value={status}
                  onChange={(e) => { setStatus(e.target.value); setPage(1); }}>
            {STATUSES.map(s => <option key={s} value={s}>{s || "All statuses"}</option>)}
          </select>
          <button onClick={() => refetch()} className="btn-secondary"><RefreshCw className="w-4 h-4" /></button>
        </div>

        {/* Table */}
        <div className="card p-0 overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-slate-200 dark:border-slate-800">
                  {["User", "Role", "Status", "Joined", "Last Active", ""].map((h) => (
                    <th key={h} className="text-left px-4 py-3 text-xs font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wider whitespace-nowrap">
                      {h}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-200 dark:divide-slate-800/50">
                {isLoading && <tr><td colSpan={6} className="py-12 text-center text-slate-500">Loading...</td></tr>}
                {users.map((u: any) => (
                  <tr key={u.id} className="hover:bg-slate-50 dark:hover:bg-slate-800/30 transition-colors">
                    <td className="px-4 py-3">
                      <div className="flex items-center gap-3">
                        <div className="w-8 h-8 rounded-full bg-gradient-to-br from-indigo-400 to-violet-500 flex items-center justify-center text-white text-sm font-bold shrink-0">
                          {u.full_name?.charAt(0).toUpperCase()}
                        </div>
                        <div>
                          <p className="font-medium text-slate-900 dark:text-white">{u.full_name}</p>
                          <p className="text-xs text-slate-500">{u.email}</p>
                        </div>
                      </div>
                    </td>
                    <td className="px-4 py-3 capitalize text-slate-600 dark:text-slate-400">{u.role}</td>
                    <td className="px-4 py-3">
                      <span className={`badge ${u.status === "active" ? "badge-resolved" : u.status === "suspended" ? "badge-urgent" : "badge-closed"}`}>
                        {u.status}
                      </span>
                    </td>
                    <td className="px-4 py-3 text-slate-500 dark:text-slate-400 text-xs">
                      {u.created_at ? format(new Date(u.created_at), "MMM d, yyyy") : "—"}
                    </td>
                    <td className="px-4 py-3 text-slate-500 dark:text-slate-400 text-xs">
                      {u.last_login_at ? format(new Date(u.last_login_at), "MMM d, HH:mm") : "Never"}
                    </td>
                    <td className="px-4 py-3">
                      <div className="flex items-center gap-1 justify-end">
                        <button onClick={() => setEditingUser(u)} title="Edit"
                                className="p-1.5 text-slate-400 hover:text-indigo-400 hover:bg-indigo-900/20 rounded-lg transition-all">
                          <Edit2 className="w-4 h-4" />
                        </button>
                        <button onClick={() => { if(confirm("Are you sure you want to permanently delete this user? This action cannot be undone.")) hardDelete.mutate(u.id); }} title="Delete"
                                className="p-1.5 text-slate-400 hover:text-rose-400 hover:bg-rose-900/20 rounded-lg transition-all">
                          <Trash2 className="w-4 h-4" />
                        </button>
                        {u.status === "active" ? (
                          <button onClick={() => { if(confirm("Are you sure you want to deactivate this user?")) deactivate.mutate(u.id); }} title="Deactivate"
                                  className="p-1.5 text-slate-400 hover:text-orange-400 hover:bg-orange-900/20 rounded-lg transition-all">
                            <UserX className="w-4 h-4" />
                          </button>
                        ) : (
                          <button onClick={() => activate.mutate(u.id)} title="Activate"
                                  className="p-1.5 text-slate-400 hover:text-emerald-400 hover:bg-emerald-900/20 rounded-lg transition-all">
                            <UserCheck className="w-4 h-4" />
                          </button>
                        )}
                        {u.mfa_enabled && (
                          <span title="MFA enabled" className="ml-1">
                            <ShieldCheck className="w-4 h-4 text-emerald-400" />
                          </span>
                        )}
                      </div>
                    </td>
                  </tr>
                ))}
                {!isLoading && users.length === 0 && (
                  <tr><td colSpan={6} className="py-12 text-center text-slate-500">No users found</td></tr>
                )}
              </tbody>
            </table>
          </div>
        </div>
      </div>
      {showCreate && <CreateUserModal onClose={() => setShowCreate(false)} onCreated={() => { qc.invalidateQueries({ queryKey: ["users"] }); setShowCreate(false); }} />}
      {editingUser && <EditUserModal user={editingUser} onClose={() => setEditingUser(null)} onUpdated={() => { qc.invalidateQueries({ queryKey: ["users"] }); setEditingUser(null); }} />}
    </div>
  );
}




