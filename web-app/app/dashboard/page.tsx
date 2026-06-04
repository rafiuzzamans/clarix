"use client";

import { useQuery } from "@tanstack/react-query";
import { analyticsApi, casesApi } from "@/lib/api";
import { useAuth } from "@/lib/auth-context";
import TopBar from "@/components/layout/TopBar";
import {
  AreaChart, Area, BarChart, Bar, PieChart, Pie, Cell, XAxis, YAxis,
  CartesianGrid, Tooltip, ResponsiveContainer, Legend,
} from "recharts";
import {
  Ticket, TrendingUp, AlertTriangle, CheckCircle,
  Clock, Users, Activity, ArrowUp,
} from "lucide-react";
import { format } from "date-fns";

const COLORS = ["#6366f1", "#8b5cf6", "#06b6d4", "#10b981", "#f59e0b", "#ef4444"];
const SENTIMENT_COLORS = { positive: "#10b981", neutral: "#6366f1", negative: "#ef4444" };

function StatCard({ label, value, icon: Icon, color, delta }: any) {
  return (
    <div className="card-hover animate-fade-in flex flex-col justify-between">
      <div className="flex items-center gap-2 mb-3">
        <div className={`p-1.5 rounded-full ${color}`}>
          <Icon className="w-4 h-4 text-white" />
        </div>
        <p className="text-xs font-bold uppercase tracking-wider text-slate-500 dark:text-slate-400">{label}</p>
      </div>
      <p className="text-5xl font-extrabold tracking-tighter text-slate-900 dark:text-white">{value ?? "—"}</p>
      {delta !== undefined && (
        <div className="flex items-center gap-1 mt-3">
          <ArrowUp className="w-3.5 h-3.5 text-emerald-500" />
          <span className="text-xs font-bold text-emerald-500">{delta} today</span>
        </div>
      )}
    </div>
  );
}

export default function DashboardPage() {
  const { user } = useAuth();

  const { data: overview } = useQuery({
    queryKey: ["analytics-overview"],
    queryFn: () => analyticsApi.overview().then((r) => r.data),
    refetchInterval: 30_000,
  });

  const { data: volumeData } = useQuery({
    queryKey: ["case-volume"],
    queryFn: () => analyticsApi.caseVolume(14).then((r) => r.data?.data ?? []),
  });

  const { data: sentimentData } = useQuery({
    queryKey: ["sentiment-trend"],
    queryFn: () => analyticsApi.sentimentTrend(14).then((r) => r.data?.data ?? []),
  });

  const { data: priorityData } = useQuery({
    queryKey: ["priority-breakdown"],
    queryFn: () => analyticsApi.priorityBreakdown().then((r) => r.data?.data ?? []),
  });

  const { data: recentCases } = useQuery({
    queryKey: ["recent-cases"],
    queryFn: () => casesApi.list({ page: 1, page_size: 5 }).then((r) => r.data?.items ?? []),
  });

  const isManager = user?.role === "manager" || user?.role === "admin" || user?.role === "supervisor";

  return (
    <div className="animate-fade-in">
      <TopBar
        title="Dashboard"
        subtitle={`Welcome back, ${user?.full_name?.split(" ")[0]} 👋`}
      />

      <div className="p-6 space-y-6">

        {/* KPI Stats */}
        {isManager && (
          <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
            <StatCard label="Open Cases"     value={overview?.open_cases}     icon={Ticket}        color="bg-indigo-600"   delta={overview?.cases_today} />
            <StatCard label="Resolved"       value={overview?.resolved_cases} icon={CheckCircle}   color="bg-emerald-600" />
            <StatCard label="Escalated"      value={overview?.escalated_cases} icon={AlertTriangle} color="bg-orange-600"  />
            <StatCard label="Avg Resolution" value={overview?.avg_resolution_hours ? `${overview.avg_resolution_hours}h` : "—"} icon={Clock} color="bg-violet-600" />
          </div>
        )}

        {/* Customer: just their cases summary */}
        {user?.role === "customer" && (
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
            <StatCard label="My Open Cases"    value={overview?.open_cases}     icon={Ticket}      color="bg-indigo-600" />
            <StatCard label="Resolved"         value={overview?.resolved_cases} icon={CheckCircle} color="bg-emerald-600" />
            <StatCard label="Cases This Week"  value={overview?.cases_this_week} icon={Activity}   color="bg-violet-600" />
          </div>
        )}

        {/* Charts row */}
        {isManager && (
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Case Volume */}
            <div className="card">
              <h3 className="text-base font-semibold text-slate-900 dark:text-white mb-4">Case Volume — Last 14 Days</h3>
              <ResponsiveContainer width="100%" height={220}>
                <AreaChart data={volumeData}>
                  <defs>
                    <linearGradient id="grad-total" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%"  stopColor="#6366f1" stopOpacity={0.3} />
                      <stop offset="95%" stopColor="#6366f1" stopOpacity={0} />
                    </linearGradient>
                  </defs>
                  <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
                  <XAxis dataKey="day" tick={{ fill: "#64748b", fontSize: 11 }}
                         tickFormatter={(v) => format(new Date(v), "MMM d")} />
                  <YAxis tick={{ fill: "#64748b", fontSize: 11 }} />
                  <Tooltip
                    contentStyle={{ background: "#0f172a", border: "1px solid #1e293b", borderRadius: "12px" }}
                    labelStyle={{ color: "#94a3b8" }}
                  />
                  <Area type="monotone" dataKey="total"    stroke="#6366f1" fill="url(#grad-total)" strokeWidth={2} name="Total" />
                  <Area type="monotone" dataKey="resolved" stroke="#10b981" fill="none" strokeWidth={2} strokeDasharray="4 4" name="Resolved" />
                </AreaChart>
              </ResponsiveContainer>
            </div>

            {/* Sentiment Trend */}
            <div className="card">
              <h3 className="text-base font-semibold text-slate-900 dark:text-white mb-4">Sentiment Trend</h3>
              <ResponsiveContainer width="100%" height={220}>
                <BarChart data={sentimentData}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
                  <XAxis dataKey="day" tick={{ fill: "#64748b", fontSize: 11 }}
                         tickFormatter={(v) => format(new Date(v), "MMM d")} />
                  <YAxis tick={{ fill: "#64748b", fontSize: 11 }} />
                  <Tooltip contentStyle={{ background: "#0f172a", border: "1px solid #1e293b", borderRadius: "12px" }} />
                  <Legend />
                  <Bar dataKey="positive" fill="#10b981" radius={[4,4,0,0]} name="Positive" stackId="a" />
                  <Bar dataKey="neutral"  fill="#6366f1" radius={[0,0,0,0]} name="Neutral"  stackId="a" />
                  <Bar dataKey="negative" fill="#ef4444" radius={[4,4,0,0]} name="Negative" stackId="a" />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </div>
        )}

        {/* Priority pie + recent cases */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {isManager && (
            <div className="card">
              <h3 className="text-base font-semibold text-slate-900 dark:text-white mb-4">Priority Breakdown</h3>
              <ResponsiveContainer width="100%" height={200}>
                <PieChart>
                  <Pie data={priorityData} cx="50%" cy="50%" innerRadius={55} outerRadius={80}
                       dataKey="total" nameKey="priority" paddingAngle={3}>
                    {priorityData?.map((_: any, i: number) => (
                      <Cell key={i} fill={COLORS[i % COLORS.length]} />
                    ))}
                  </Pie>
                  <Tooltip contentStyle={{ background: "#0f172a", border: "1px solid #1e293b", borderRadius: "12px" }} />
                  <Legend
                    formatter={(v) => <span className="text-xs text-slate-400 capitalize">{v}</span>}
                  />
                </PieChart>
              </ResponsiveContainer>
            </div>
          )}

          {/* Recent Cases */}
          <div className={`card ${isManager ? "lg:col-span-2" : "lg:col-span-3"}`}>
            <h3 className="text-base font-semibold text-slate-900 dark:text-white mb-4">Recent Cases</h3>
            <div className="space-y-2">
              {recentCases?.length === 0 && (
                <p className="text-slate-500 text-sm text-center py-8">No cases yet</p>
              )}
              {recentCases?.map((c: any) => (
                <a key={c.id} href={`/dashboard/cases/${c.id}`}
                   className="flex items-center justify-between p-3 rounded-xl bg-slate-50/50 dark:bg-slate-800/50
                              hover:bg-slate-100 dark:hover:bg-slate-800 border border-slate-200 dark:border-slate-700/50 transition-all group">
                  <div className="min-w-0">
                    <p className="text-sm font-medium text-slate-800 dark:text-white group-hover:text-indigo-600 dark:group-hover:text-indigo-300 truncate">
                      #{c.case_number} — {c.title}
                    </p>
                    <p className="text-xs text-slate-500 mt-0.5">
                      {format(new Date(c.created_at), "MMM d, HH:mm")} · {c.source}
                    </p>
                  </div>
                  <div className="flex items-center gap-2 shrink-0 ml-3">
                    <span className={`badge-${c.priority}`}>{c.priority}</span>
                    <span className={`badge-${c.status}`}>{c.status?.replace("_"," ")}</span>
                  </div>
                </a>
              ))}
            </div>
          </div>
        </div>

      </div>
    </div>
  );
}

# Add real-time case count badge

# Add trend indicator to KPIs
