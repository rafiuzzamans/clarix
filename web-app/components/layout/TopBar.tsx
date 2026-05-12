"use client";

import { Bell, Wifi, WifiOff } from "lucide-react";
import { useAuth } from "@/lib/auth-context";

interface TopBarProps {
  title: string;
  subtitle?: string;
  actions?: React.ReactNode;
}

export default function TopBar({ title, subtitle, actions }: TopBarProps) {
  const { user, isMockMode } = useAuth();

  return (
    <>
      {isMockMode && (
        <div className="flex items-center gap-2 bg-amber-500/10 border-b border-amber-500/20 px-6 py-2">
          <WifiOff className="w-3.5 h-3.5 text-amber-400 shrink-0" />
          <p className="text-xs text-amber-300">
            <span className="font-semibold">Demo mode</span> — backend offline. Data is mocked; API actions are disabled.
          </p>
        </div>
      )}
      <header className="bg-slate-900/80 backdrop-blur border-b border-slate-800 px-6 py-4 flex items-center justify-between">
        <div>
          <h1 className="text-xl font-bold text-white">{title}</h1>
          {subtitle && <p className="text-sm text-slate-400 mt-0.5">{subtitle}</p>}
        </div>

        <div className="flex items-center gap-3">
          {actions}

          {/* Online / offline indicator */}
          <div className={`flex items-center gap-1.5 px-2.5 py-1 rounded-lg text-xs font-medium ${
            isMockMode
              ? "bg-amber-500/10 border border-amber-500/20 text-amber-400"
              : "bg-emerald-500/10 border border-emerald-500/20 text-emerald-400"
          }`}>
            {isMockMode
              ? <><WifiOff className="w-3 h-3" /> Offline</>
              : <><Wifi className="w-3 h-3" /> Live</>
            }
          </div>

          <button
            id="topbar-notifications"
            className="relative p-2 rounded-xl bg-slate-800 text-slate-400 hover:text-white hover:bg-slate-700 transition-all"
          >
            <Bell className="w-5 h-5" />
            <span className="absolute top-1 right-1 w-2 h-2 bg-indigo-500 rounded-full" />
          </button>

          <div className="flex items-center gap-2 bg-slate-800 rounded-xl px-3 py-2 border border-slate-700">
            <div className="w-6 h-6 rounded-full bg-gradient-to-br from-indigo-400 to-violet-500 flex items-center justify-center text-white text-xs font-bold">
              {user?.full_name?.[0] ?? "?"}
            </div>
            <span className="text-sm text-slate-300 hidden sm:block">{user?.full_name}</span>
            {isMockMode && (
              <span className="text-xs bg-amber-500/20 text-amber-300 px-1.5 py-0.5 rounded capitalize">
                {user?.role}
              </span>
            )}
          </div>
        </div>
      </header>
    </>
  );
}
