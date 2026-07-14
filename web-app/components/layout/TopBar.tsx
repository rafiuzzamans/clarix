"use client";

import { Bell, Wifi, Sun, Moon, CheckCheck, BellOff } from "lucide-react";
import { useAuth } from "@/lib/auth-context";
import { useTheme } from "@/components/providers/ThemeProvider";
import { notificationsApi } from "@/lib/api";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { useState, useRef, useEffect } from "react";
import { format } from "date-fns";

interface TopBarProps {
  title: string;
  subtitle?: string;
  actions?: React.ReactNode;
}

interface Notification {
  id: string;
  subject: string | null;
  body: string;
  type: string;
  read_at: string | null;
  created_at: string;
  reference_type: string | null;
  reference_id: string | null;
}

export default function TopBar({ title, subtitle, actions }: TopBarProps) {
  const { user } = useAuth();
  const { theme, toggleTheme } = useTheme();
  const [open, setOpen] = useState(false);
  const panelRef = useRef<HTMLDivElement>(null);
  const queryClient = useQueryClient();

  // Fetch inbox every 30 seconds
  const { data } = useQuery({
    queryKey: ["notifications-inbox", user?.id],
    queryFn: () => notificationsApi.inbox(user!.id).then((r) => r.data),
    enabled: !!user?.id,
    refetchInterval: 30_000,
  });

  const notifications: Notification[] = data?.notifications ?? [];
  const unreadCount = notifications.filter((n) => !n.read_at).length;

  const markReadMutation = useMutation({
    mutationFn: (id: string) => notificationsApi.markRead(id),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["notifications-inbox", user?.id] }),
  });

  const markAllRead = () => {
    notifications.filter((n) => !n.read_at).forEach((n) => markReadMutation.mutate(n.id));
  };

  // Close on outside click
  useEffect(() => {
    const handler = (e: MouseEvent) => {
      if (panelRef.current && !panelRef.current.contains(e.target as Node)) {
        setOpen(false);
      }
    };
    document.addEventListener("mousedown", handler);
    return () => document.removeEventListener("mousedown", handler);
  }, []);

  return (
    <>
      <header className="bg-white/70 dark:bg-black/40 backdrop-blur-3xl border-b border-slate-200 dark:border-white/5 px-6 py-4 flex items-center justify-between sticky top-0 z-50 transition-colors">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight text-slate-900 dark:text-white">{title}</h1>
          {subtitle && <p className="text-sm text-slate-500 dark:text-white/50 mt-1 font-medium">{subtitle}</p>}
        </div>

        <div className="flex items-center gap-4">
          {actions}

          {/* Online indicator */}
          <div className="flex items-center gap-1.5 px-3 py-1.5 rounded-full text-xs font-semibold uppercase tracking-wider bg-emerald-100 border border-emerald-200 text-emerald-600 dark:bg-emerald-500/10 dark:border-emerald-500/20 dark:text-emerald-400">
            <Wifi className="w-3.5 h-3.5" /> Live
          </div>

          {/* Theme toggle */}
          <button
            onClick={toggleTheme}
            className="relative p-2.5 rounded-full bg-slate-100 text-slate-500 hover:text-slate-900 hover:bg-slate-200 dark:bg-white/5 dark:text-white/60 dark:hover:text-white dark:hover:bg-white/10 transition-all border border-transparent dark:hover:border-white/10"
          >
            {theme === "dark" ? <Sun className="w-5 h-5" /> : <Moon className="w-5 h-5" />}
          </button>

          {/* Notification bell */}
          <div className="relative" ref={panelRef}>
            <button
              id="topbar-notifications"
              onClick={() => setOpen((v) => !v)}
              className="relative p-2.5 rounded-full bg-slate-100 text-slate-500 hover:text-slate-900 hover:bg-slate-200 dark:bg-white/5 dark:text-white/60 dark:hover:text-white dark:hover:bg-white/10 transition-all border border-transparent dark:hover:border-white/10"
            >
              <Bell className="w-5 h-5" />
              {unreadCount > 0 && (
                <span className="absolute top-1 right-1 min-w-[18px] h-[18px] flex items-center justify-center bg-red-500 text-white text-[10px] font-bold rounded-full border-2 border-white dark:border-black px-0.5">
                  {unreadCount > 9 ? "9+" : unreadCount}
                </span>
              )}
            </button>

            {/* Dropdown panel */}
            {open && (
              <div className="absolute right-0 mt-2 w-96 max-h-[520px] flex flex-col rounded-2xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-white/10 shadow-2xl shadow-slate-900/20 dark:shadow-black/60 overflow-hidden z-50 animate-fade-in">
                {/* Header */}
                <div className="flex items-center justify-between px-4 py-3 border-b border-slate-100 dark:border-white/5">
                  <div className="flex items-center gap-2">
                    <Bell className="w-4 h-4 text-indigo-500" />
                    <span className="font-semibold text-slate-900 dark:text-white text-sm">Notifications</span>
                    {unreadCount > 0 && (
                      <span className="bg-indigo-100 dark:bg-indigo-500/20 text-indigo-600 dark:text-indigo-400 text-[11px] font-bold px-2 py-0.5 rounded-full">
                        {unreadCount} new
                      </span>
                    )}
                  </div>
                  {unreadCount > 0 && (
                    <button
                      onClick={markAllRead}
                      className="text-xs text-slate-500 dark:text-white/40 hover:text-indigo-600 dark:hover:text-indigo-400 flex items-center gap-1 transition-colors"
                    >
                      <CheckCheck className="w-3.5 h-3.5" /> Mark all read
                    </button>
                  )}
                </div>

                {/* Notification list */}
                <div className="overflow-y-auto flex-1">
                  {notifications.length === 0 ? (
                    <div className="flex flex-col items-center justify-center py-12 gap-3 text-slate-400 dark:text-white/30">
                      <BellOff className="w-8 h-8" />
                      <p className="text-sm font-medium">No notifications yet</p>
                    </div>
                  ) : (
                    notifications.map((n) => (
                      <div
                        key={n.id}
                        onClick={() => { if (!n.read_at) markReadMutation.mutate(n.id); }}
                        className={`px-4 py-3 border-b border-slate-100 dark:border-white/5 last:border-0 cursor-pointer transition-colors hover:bg-slate-50 dark:hover:bg-white/5 ${
                          !n.read_at ? "bg-indigo-50/60 dark:bg-indigo-500/5" : ""
                        }`}
                      >
                        <div className="flex items-start gap-2.5">
                          {/* Unread dot */}
                          <div className={`mt-1.5 w-2 h-2 rounded-full shrink-0 ${!n.read_at ? "bg-indigo-500" : "bg-transparent"}`} />
                          <div className="flex-1 min-w-0">
                            {n.subject && (
                              <p className={`text-sm font-semibold truncate ${!n.read_at ? "text-slate-900 dark:text-white" : "text-slate-600 dark:text-white/60"}`}>
                                {n.subject}
                              </p>
                            )}
                            <p className={`text-xs mt-0.5 line-clamp-2 ${!n.read_at ? "text-slate-700 dark:text-white/70" : "text-slate-400 dark:text-white/40"}`}>
                              {n.body}
                            </p>
                            <p className="text-[10px] text-slate-400 dark:text-white/30 mt-1">
                              {format(new Date(n.created_at), "MMM d, HH:mm")}
                            </p>
                          </div>
                        </div>
                      </div>
                    ))
                  )}
                </div>
              </div>
            )}
          </div>

          {/* User pill */}
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
