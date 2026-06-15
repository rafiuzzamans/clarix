"use client";

import { Bell, Wifi, Sun, Moon } from "lucide-react";
import { useAuth } from "@/lib/auth-context";
import { useTheme } from "@/components/providers/ThemeProvider";

interface TopBarProps {
  title: string;
  subtitle?: string;
  actions?: React.ReactNode;
}

export default function TopBar({ title, subtitle, actions }: TopBarProps) {
  const { user } = useAuth();
  const { theme, toggleTheme } = useTheme();

  return (
    <>
      <header className="bg-white/70 dark:bg-black/40 backdrop-blur-3xl border-b border-slate-200 dark:border-white/5 px-6 py-4 flex items-center justify-between sticky top-0 z-50 transition-colors">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight text-slate-900 dark:text-white">{title}</h1>
          {subtitle && <p className="text-sm text-slate-500 dark:text-white/50 mt-1 font-medium">{subtitle}</p>}
        </div>

        <div className="flex items-center gap-4">
          {actions}

          {/* Online / offline indicator */}
          <div className="flex items-center gap-1.5 px-3 py-1.5 rounded-full text-xs font-semibold uppercase tracking-wider bg-emerald-100 border border-emerald-200 text-emerald-600 dark:bg-emerald-500/10 dark:border-emerald-500/20 dark:text-emerald-400">
            <Wifi className="w-3.5 h-3.5" /> Live
          </div>

          <button
            onClick={toggleTheme}
            className="relative p-2.5 rounded-full bg-slate-100 text-slate-500 hover:text-slate-900 hover:bg-slate-200 dark:bg-white/5 dark:text-white/60 dark:hover:text-white dark:hover:bg-white/10 transition-all border border-transparent dark:hover:border-white/10"
          >
            {theme === 'dark' ? <Sun className="w-5 h-5" /> : <Moon className="w-5 h-5" />}
          </button>

          <button
            id="topbar-notifications"
            className="relative p-2.5 rounded-full bg-slate-100 text-slate-500 hover:text-slate-900 hover:bg-slate-200 dark:bg-white/5 dark:text-white/60 dark:hover:text-white dark:hover:bg-white/10 transition-all border border-transparent dark:hover:border-white/10"
          >
            <Bell className="w-5 h-5" />
            <span className="absolute top-1.5 right-1.5 w-2.5 h-2.5 bg-red-500 rounded-full border-2 border-white dark:border-black" />
          </button>

          <div className="flex items-center gap-3 bg-slate-100 dark:bg-white/5 rounded-full pl-2 pr-4 py-1.5 border border-slate-200 dark:border-white/5 hover:bg-slate-200 dark:hover:bg-white/10 transition-all cursor-pointer">
            <div className="w-8 h-8 rounded-full bg-gradient-to-br from-indigo-500 to-purple-600 flex items-center justify-center text-white text-sm font-bold shadow-lg shadow-indigo-500/20">
              {user?.full_name?.[0] ?? "?"}
            </div>
            <span className="text-sm font-medium text-slate-700 dark:text-white/90 hidden sm:block">{user?.full_name}</span>
            <span className="text-[10px] uppercase font-bold tracking-wider bg-slate-200 dark:bg-white/10 text-slate-600 dark:text-white/70 px-2 py-0.5 rounded-full">
              {user?.role}
            </span>
          </div>
        </div>
      </header>
    </>
  );
}

# Add user role badge

# Add keyboard shortcut hint

# Add notification dropdown
