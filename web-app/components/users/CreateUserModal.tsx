"use client";

import { useState } from "react";
import { X, Loader2 } from "lucide-react";
import { usersApi } from "@/lib/api";
import toast from "react-hot-toast";

interface Props {
  onClose: () => void;
  onCreated: () => void;
}

export default function CreateUserModal({ onClose, onCreated }: Props) {
  const [loading, setLoading] = useState(false);
  const [form, setForm] = useState({
    full_name: "",
    email: "",
    password: "",
    role: "customer"
  });

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    try {
      await usersApi.create(form);
      toast.success("User created successfully!");
      onCreated();
    } catch (error: any) {
      toast.error(error.response?.data?.detail || "Failed to create user");
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
        
        <h2 className="text-xl font-bold text-slate-900 dark:text-white mb-6">Create New User</h2>
        
        <form onSubmit={handleSubmit} className="space-y-5">
          <div>
            <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1.5">Full Name</label>
            <input required type="text" className="input-field" value={form.full_name} onChange={e => setForm({...form, full_name: e.target.value})} placeholder="e.g. John Doe" />
          </div>
          <div>
            <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1.5">Email Address</label>
            <input required type="email" className="input-field" value={form.email} onChange={e => setForm({...form, email: e.target.value})} placeholder="john@example.com" />
          </div>
          <div className="grid grid-cols-1 gap-5">
            <div>
              <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1.5">Role</label>
              <select className="input-field" value={form.role} onChange={e => setForm({...form, role: e.target.value})}>
                <option value="customer">Customer</option>
                <option value="agent">Agent</option>
                <option value="supervisor">Supervisor</option>
                <option value="manager">Manager</option>
                <option value="admin">Admin</option>
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1.5">Password</label>
              <input required type="password" minLength={8} className="input-field" value={form.password} onChange={e => setForm({...form, password: e.target.value})} placeholder="At least 8 chars, 1 uppercase, 1 digit" />
            </div>
          </div>

          <div className="pt-6 flex gap-3 justify-end">
            <button type="button" onClick={onClose} className="btn-secondary">Cancel</button>
            <button type="submit" disabled={loading} className="btn-primary min-w-[120px]">
              {loading ? <Loader2 className="w-5 h-5 animate-spin mx-auto" /> : "Create User"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
