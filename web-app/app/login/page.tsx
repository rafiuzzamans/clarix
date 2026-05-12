"use client";

import { useState } from "react";
import { useAuth } from "@/lib/auth-context";
import { useRouter } from "next/navigation";
import toast from "react-hot-toast";
import { Shield, Eye, EyeOff, Loader2, Bot } from "lucide-react";

export default function LoginPage() {
  const { login } = useAuth();
  const router = useRouter();
  const [form, setForm] = useState({ email: "", password: "", mfa_code: "" });
  const [showPassword, setShowPassword] = useState(false);
  const [showMfa, setShowMfa] = useState(false);
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    try {
      await login(form.email, form.password, form.mfa_code || undefined);
      toast.success("Welcome back!");
      router.push("/dashboard");
    } catch (err: any) {
      const msg = err?.response?.data?.detail;
      if (msg === "MFA code required") {
        setShowMfa(true);
        toast("Please enter your MFA code", { icon: "🔐" });
      } else {
        toast.error(msg || "Invalid credentials");
      }
    } finally {
      setLoading(false);
    }
  };

  const demoAccounts = [
    { label: "Admin",      email: "admin@csplatform.local" },
    { label: "Manager",    email: "manager@csplatform.local" },
    { label: "Agent",      email: "agent1@csplatform.local" },
    { label: "Customer",   email: "customer@csplatform.local" },
  ];

  return (
    <div className="min-h-screen bg-slate-950 flex items-center justify-center p-4 relative overflow-hidden">
      {/* Background glow */}
      <div className="absolute inset-0 overflow-hidden pointer-events-none">
        <div className="absolute -top-40 -left-40 w-96 h-96 bg-indigo-600/20 rounded-full blur-3xl" />
        <div className="absolute -bottom-40 -right-40 w-96 h-96 bg-violet-600/20 rounded-full blur-3xl" />
        <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[600px] h-[600px] bg-indigo-500/5 rounded-full blur-3xl" />
      </div>

      <div className="w-full max-w-md animate-fade-in relative z-10">
        {/* Logo */}
        <div className="text-center mb-8">
          <div className="inline-flex items-center justify-center w-16 h-16 rounded-2xl bg-gradient-to-br from-indigo-500 to-violet-600 shadow-2xl shadow-indigo-500/40 mb-4">
            <Bot className="w-8 h-8 text-white" />
          </div>
          <h1 className="text-3xl font-bold text-gradient">CS Platform</h1>
          <p className="text-slate-400 mt-2 text-sm">AI-Powered Customer Service Intelligence</p>
        </div>

        {/* Card */}
        <div className="card border-slate-700/50">
          <div className="flex items-center gap-2 mb-6">
            <Shield className="w-5 h-5 text-indigo-400" />
            <h2 className="text-lg font-semibold text-white">Sign in to your account</h2>
          </div>

          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-slate-300 mb-1.5">Email address</label>
              <input
                id="email"
                type="email"
                required
                className="input-field"
                placeholder="you@company.com"
                value={form.email}
                onChange={(e) => setForm({ ...form, email: e.target.value })}
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-slate-300 mb-1.5">Password</label>
              <div className="relative">
                <input
                  id="password"
                  type={showPassword ? "text" : "password"}
                  required
                  className="input-field pr-12"
                  placeholder="••••••••"
                  value={form.password}
                  onChange={(e) => setForm({ ...form, password: e.target.value })}
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-200"
                >
                  {showPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                </button>
              </div>
            </div>

            {showMfa && (
              <div className="animate-fade-in">
                <label className="block text-sm font-medium text-slate-300 mb-1.5">
                  🔐 MFA Verification Code
                </label>
                <input
                  id="mfa_code"
                  type="text"
                  className="input-field tracking-widest text-center text-xl"
                  placeholder="000000"
                  maxLength={6}
                  value={form.mfa_code}
                  onChange={(e) => setForm({ ...form, mfa_code: e.target.value })}
                />
              </div>
            )}

            <button id="login-btn" type="submit" disabled={loading} className="btn-primary w-full justify-center mt-2">
              {loading ? (
                <><Loader2 className="w-4 h-4 animate-spin" /> Signing in...</>
              ) : (
                "Sign in"
              )}
            </button>
          </form>

          {/* Demo accounts */}
          <div className="mt-6 pt-6 border-t border-slate-800">
            <p className="text-xs text-slate-500 mb-3 text-center">Quick demo login (password: <code className="text-indigo-400">Admin@123</code>)</p>
            <div className="grid grid-cols-2 gap-2">
              {demoAccounts.map((acc) => (
                <button
                  key={acc.email}
                  id={`demo-${acc.label.toLowerCase()}`}
                  onClick={() => setForm({ ...form, email: acc.email, password: "Admin@123" })}
                  className="text-xs bg-slate-800 hover:bg-slate-700 border border-slate-700 
                             text-slate-300 px-3 py-2 rounded-lg transition-all duration-200"
                >
                  {acc.label}
                </button>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
