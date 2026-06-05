"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useAuth } from "@/lib/auth-context";
import { clsx } from "clsx";
import {
  LayoutDashboard, Ticket, Users, BarChart3, MessageSquare,
  FileText, Settings, LogOut, Bot, Bell, ChevronLeft,
} from "lucide-react";
import { useState } from "react";
import toast from "react-hot-toast";

const navItems = [
  { href: "/dashboard",           label: "Overview",       icon: LayoutDashboard, roles: ["admin","manager","supervisor","agent","customer"] },
  { href: "/dashboard/cases",     label: "Cases",          icon: Ticket,           roles: ["admin","manager","supervisor","agent","customer"] },
  { href: "/dashboard/chatbot",   label: "Chatbot",        icon: Bot,              roles: ["admin","manager","supervisor","agent","customer"] },
  { href: "/dashboard/analytics", label: "Analytics",      icon: BarChart3,        roles: ["admin","manager","supervisor"] },
  { href: "/dashboard/users",     label: "Users",          icon: Users,            roles: ["admin","manager"] },
  { href: "/dashboard/audit",     label: "Audit Logs",     icon: FileText,         roles: ["admin"] },
  { href: "/dashboard/admin",     label: "Admin",          icon: Settings,         roles: ["admin"] },
];

export default function Sidebar() {
  const { user, logout, isRole } = useAuth();
  const pathname = usePathname();
  const [collapsed, setCollapsed] = useState(false);

  const handleLogout = async () => {
    await logout();
    toast.success("Logged out");
  };

  const visibleItems = navItems.filter((item) =>
    item.roles.some((r) => user?.role === r)
  );

  return (
    <aside
      className={clsx(
        "h-screen bg-slate-50 border-r border-slate-200 dark:bg-black dark:border-white/5 flex flex-col transition-all duration-300",
        collapsed ? "w-20" : "w-[260px]"
      )}
    >
      {/* Header */}
      <div className="flex items-center justify-between p-6">
        {!collapsed && (
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 rounded-full bg-indigo-600 dark:bg-white flex items-center justify-center shrink-0 shadow-lg shadow-indigo-600/20 dark:shadow-white/20">
              <Bot className="w-5 h-5 text-white dark:text-black" />
            </div>
            <span className="font-extrabold text-slate-900 dark:text-white text-lg tracking-wide uppercase">Clarix</span>
          </div>
        )}
        {collapsed && (
          <div className="w-9 h-9 rounded-full bg-indigo-600 dark:bg-white flex items-center justify-center mx-auto shadow-lg shadow-indigo-600/20 dark:shadow-white/20">
            <Bot className="w-5 h-5 text-white dark:text-black" />
          </div>
        )}
        <button
          onClick={() => setCollapsed(!collapsed)}
          className={clsx(
            "text-slate-400 hover:text-slate-700 dark:text-white/40 dark:hover:text-white transition-colors p-1.5 rounded-lg hover:bg-slate-200 dark:hover:bg-white/5",
            collapsed && "mx-auto mt-4"
          )}
          id="sidebar-toggle"
        >
          <ChevronLeft className={clsx("w-4 h-4 transition-transform", collapsed && "rotate-180")} />
        </button>
      </div>

      {/* User badge */}
      {!collapsed && user && (
        <div className="mx-4 mt-2 mb-4 p-3.5 bg-white dark:bg-white/5 rounded-2xl border border-slate-200 dark:border-white/5 shadow-sm dark:shadow-inner">
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 rounded-full bg-indigo-500 flex items-center justify-center text-white text-sm font-bold shrink-0">
              {user?.full_name?.[0] ?? "?"}
            </div>
            <div className="min-w-0">
              <p className="text-sm font-bold text-slate-900 dark:text-white truncate">{user?.full_name}</p>
              <p className="text-xs text-indigo-600 dark:text-blue-500 font-medium capitalize mt-0.5">{user?.role}</p>
            </div>
          </div>
        </div>
      )}

      {/* Navigation */}
      <nav className="flex-1 px-4 space-y-1.5 mt-2 overflow-y-auto">
        {visibleItems.map((item) => {
          const Icon = item.icon;
          const active = pathname === item.href || (item.href !== "/dashboard" && pathname.startsWith(item.href));
          return (
            <Link key={item.href} href={item.href} id={`nav-${item.label.toLowerCase().replace(" ","-")}`}>
              <div className={clsx(
                "flex items-center gap-3 px-4 py-3 rounded-2xl transition-all duration-300 cursor-pointer font-semibold text-sm",
                active 
                  ? "bg-white text-indigo-700 shadow-md border border-slate-200 dark:bg-white dark:text-black dark:border-transparent dark:shadow-[0_0_20px_rgba(255,255,255,0.2)]" 
                  : "text-slate-500 hover:text-slate-900 hover:bg-slate-200 dark:text-white/50 dark:hover:text-white dark:hover:bg-white/5"
              )}>
                <Icon className={clsx("w-5 h-5 shrink-0", active ? "text-indigo-700 dark:text-black" : "text-slate-400 dark:text-white/40")} />
                {!collapsed && <span>{item.label}</span>}
              </div>
            </Link>
          );
        })}
      </nav>

      {/* Footer */}
      <div className="p-4">
        <button
          onClick={handleLogout}
          id="logout-btn"
          className={clsx(
            "w-full flex items-center gap-3 px-4 py-3 rounded-2xl text-slate-500 dark:text-white/40 font-semibold text-sm",
            "hover:text-red-600 hover:bg-red-50 dark:hover:text-white dark:hover:bg-white/5 transition-all duration-200"
          )}
        >
          <LogOut className="w-5 h-5 shrink-0" />
          {!collapsed && <span>Sign out</span>}
        </button>
      </div>
    </aside>
  );
}

# Add active route highlight
