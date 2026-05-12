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
        "h-screen bg-slate-900 border-r border-slate-800 flex flex-col transition-all duration-300",
        collapsed ? "w-16" : "w-64"
      )}
    >
      {/* Header */}
      <div className="flex items-center justify-between p-4 border-b border-slate-800">
        {!collapsed && (
          <div className="flex items-center gap-2">
            <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-indigo-500 to-violet-600 flex items-center justify-center shrink-0">
              <Bot className="w-4 h-4 text-white" />
            </div>
            <span className="font-bold text-white text-sm">CS Platform</span>
          </div>
        )}
        {collapsed && (
          <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-indigo-500 to-violet-600 flex items-center justify-center mx-auto">
            <Bot className="w-4 h-4 text-white" />
          </div>
        )}
        <button
          onClick={() => setCollapsed(!collapsed)}
          className={clsx(
            "text-slate-400 hover:text-white transition-colors p-1 rounded-lg hover:bg-slate-800",
            collapsed && "mx-auto mt-2"
          )}
          id="sidebar-toggle"
        >
          <ChevronLeft className={clsx("w-4 h-4 transition-transform", collapsed && "rotate-180")} />
        </button>
      </div>

      {/* User badge */}
      {!collapsed && user && (
        <div className="mx-3 mt-3 p-3 bg-slate-800/60 rounded-xl border border-slate-700/50">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 rounded-full bg-gradient-to-br from-indigo-400 to-violet-500 flex items-center justify-center text-white text-sm font-bold shrink-0">
              {user.full_name[0]}
            </div>
            <div className="min-w-0">
              <p className="text-sm font-medium text-white truncate">{user.full_name}</p>
              <p className="text-xs text-indigo-400 capitalize">{user.role}</p>
            </div>
          </div>
        </div>
      )}

      {/* Navigation */}
      <nav className="flex-1 p-3 space-y-1 mt-2 overflow-y-auto">
        {visibleItems.map((item) => {
          const Icon = item.icon;
          const active = pathname === item.href || (item.href !== "/dashboard" && pathname.startsWith(item.href));
          return (
            <Link key={item.href} href={item.href} id={`nav-${item.label.toLowerCase().replace(" ","-")}`}>
              <div className={clsx(active ? "sidebar-link-active" : "sidebar-link")}>
                <Icon className="w-5 h-5 shrink-0" />
                {!collapsed && <span className="text-sm font-medium">{item.label}</span>}
              </div>
            </Link>
          );
        })}
      </nav>

      {/* Footer */}
      <div className="p-3 border-t border-slate-800">
        <button
          onClick={handleLogout}
          id="logout-btn"
          className={clsx(
            "w-full flex items-center gap-3 px-4 py-3 rounded-xl text-slate-400",
            "hover:text-red-400 hover:bg-red-900/20 transition-all duration-200"
          )}
        >
          <LogOut className="w-5 h-5 shrink-0" />
          {!collapsed && <span className="text-sm font-medium">Sign out</span>}
        </button>
      </div>
    </aside>
  );
}
