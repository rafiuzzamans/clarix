"use client";

import { useState } from "react";
import { useAuth } from "@/lib/auth-context";
import { useTheme } from "@/components/providers/ThemeProvider";
import { useRouter } from "next/navigation";
import toast from "react-hot-toast";
import { Shield, Eye, EyeOff, Loader2, Bot, Sun, Moon } from "lucide-react";

export default function LoginPage() {
  const { login } = useAuth();
  const { theme, toggleTheme } = useTheme();
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
    { label: "Admin", email: "admin@csplatform.local" },
    { label: "Manager", email: "manager@csplatform.local" },
    { label: "Supervisor", email: "supervisor@csplatform.local" },
    { label: "Customer", email: "customer@csplatform.local" },
    { label: "Mortgage Agent", email: "agent.mortgage@csplatform.local" },
    { label: "Debt Agent", email: "agent.debt@csplatform.local" },
    { label: "Credit Agent", email: "agent.credit@csplatform.local" },
    { label: "Banking Agent", email: "agent.banking@csplatform.local" },
    { label: "Card Agent", email: "agent.card@csplatform.local" },
    { label: "Student Agent", email: "agent.student@csplatform.local" },
  ];

  return (
    <div className={`min-h-screen ${theme === 'dark' ? 'bg-black' : 'bg-slate-50'} flex items-center justify-center p-4 relative overflow-hidden transition-colors duration-500`}>
      {/* Theme Toggle */}
      <button 
        onClick={toggleTheme}
        className={`absolute top-6 right-6 p-3 rounded-full z-50 transition-all ${
          theme === 'dark' ? 'bg-white/10 text-white hover:bg-white/20' : 'bg-black/5 text-black hover:bg-black/10'
        }`}
      >
        {theme === 'dark' ? <Sun className="w-5 h-5" /> : <Moon className="w-5 h-5" />}
      </button>

      {/* Background glow */}
      <div className="absolute inset-0 overflow-hidden pointer-events-none">
        <div className={`absolute -top-[20%] -left-[10%] w-[800px] h-[800px] bg-indigo-600/20 rounded-full blur-[120px] mix-blend-screen transition-opacity ${theme === 'dark' ? 'opacity-100' : 'opacity-0'}`} />
        <div className={`absolute top-[60%] -right-[10%] w-[600px] h-[600px] bg-blue-600/10 rounded-full blur-[100px] mix-blend-screen transition-opacity ${theme === 'dark' ? 'opacity-100' : 'opacity-0'}`} />
      </div>

      <div className="w-full max-w-md animate-fade-in relative z-10">
        {/* Logo */}
        <div className="text-center mb-10">
          <div className="inline-flex items-center justify-center w-20 h-20 rounded-3xl bg-gradient-to-br from-cyan-400 to-blue-600 shadow-[0_0_40px_rgba(34,211,238,0.5)] mb-6">
            <Bot className="w-10 h-10 text-white" />
          </div>
          <h1 className={`text-4xl tracking-tight font-bold mb-3 ${theme === 'dark' ? 'text-white' : 'text-slate-900'}`}>CS Platform</h1>
          <p className={`text-base font-medium tracking-widest uppercase ${theme === 'dark' ? 'text-white/50' : 'text-slate-500'}`}>AI-Powered Customer Intelligence</p>
        </div>

        {/* Card */}
        <div className={`card ${theme === 'light' ? '!bg-white !shadow-xl !border-slate-200' : ''}`}>
          <div className="flex items-center gap-2 mb-6">
            <Shield className="w-5 h-5 text-cyan-400" />
            <h2 className={`text-lg font-semibold ${theme === 'dark' ? 'text-white' : 'text-slate-900'}`}>Sign in to your account</h2>
          </div>

          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className={`block text-sm font-medium mb-1.5 ${theme === 'dark' ? 'text-white/70' : 'text-slate-700'}`}>Email address</label>
              <input
                id="email"
                type="email"
                required
                className={`input-field ${theme === 'light' ? '!bg-slate-50 !border-slate-200 !text-slate-900' : ''}`}
                placeholder="you@company.com"
                value={form.email}
                onChange={(e) => setForm({ ...form, email: e.target.value })}
              />
            </div>

            <div>
              <label className={`block text-sm font-medium mb-1.5 ${theme === 'dark' ? 'text-white/70' : 'text-slate-700'}`}>Password</label>
              <div className="relative">
                <input
                  id="password"
                  type={showPassword ? "text" : "password"}
                  required
                  className={`input-field pr-12 ${theme === 'light' ? '!bg-slate-50 !border-slate-200 !text-slate-900' : ''}`}
                  placeholder="••••••••"
                  value={form.password}
                  onChange={(e) => setForm({ ...form, password: e.target.value })}
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className={`absolute right-3 top-1/2 -translate-y-1/2 ${theme === 'dark' ? 'text-white/40 hover:text-white/80' : 'text-slate-400 hover:text-slate-600'}`}
                >
                  {showPassword ? <EyeOff className="w-5 h-5" /> : <Eye className="w-5 h-5" />}
                </button>
              </div>
            </div>

            {showMfa && (
              <div className="animate-fade-in">
                <label className={`block text-sm font-medium mb-1.5 ${theme === 'dark' ? 'text-white/70' : 'text-slate-700'}`}>
                  🔐 MFA Verification Code
                </label>
                <input
                  id="mfa_code"
                  type="text"
                  className={`input-field tracking-widest text-center text-xl ${theme === 'light' ? '!bg-slate-50 !border-slate-200 !text-slate-900' : ''}`}
                  placeholder="000000"
                  maxLength={6}
                  value={form.mfa_code}
                  onChange={(e) => setForm({ ...form, mfa_code: e.target.value })}
                />
              </div>
            )}

            <button id="login-btn" type="submit" disabled={loading} className={`btn-primary w-full justify-center mt-2 ${theme === 'light' ? '!bg-slate-900 !text-white' : ''}`}>
              {loading ? (
                <><Loader2 className="w-5 h-5 animate-spin" /> Signing in...</>
              ) : (
                "Sign In"
              )}
            </button>
          </form>

          {/* Demo accounts */}
          <div className={`mt-8 pt-6 border-t ${theme === 'dark' ? 'border-white/10' : 'border-slate-200'}`}>
            <p className={`text-xs mb-4 text-center ${theme === 'dark' ? 'text-white/40' : 'text-slate-500'}`}>Quick demo login (password: <code className="text-cyan-400 font-bold">Admin@123</code>)</p>
            <div className="grid grid-cols-2 gap-3">
              {demoAccounts.map((acc) => (
                <button
                  key={acc.email}
                  id={`demo-${acc.label.toLowerCase().replace(' ', '-')}`}
                  onClick={() => setForm({ ...form, email: acc.email, password: "Admin@123" })}
                  className={`text-xs px-4 py-2.5 rounded-xl transition-all duration-300 font-medium ${
                    theme === 'dark' 
                      ? 'bg-white/5 hover:bg-white/10 text-white/70 border border-white/5 hover:border-white/20' 
                      : 'bg-slate-50 hover:bg-slate-100 text-slate-700 border border-slate-200'
                  }`}
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

# Add show/hide password toggle

# Add loading spinner on submit
