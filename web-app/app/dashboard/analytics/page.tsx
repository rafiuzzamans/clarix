"use client";

import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { analyticsApi } from "@/lib/api";
import TopBar from "@/components/layout/TopBar";
import {
  BarChart, Bar, PieChart, Pie, Cell, XAxis, YAxis,
  CartesianGrid, Tooltip, ResponsiveContainer, Legend, AreaChart, Area
} from "recharts";
import { format } from "date-fns";

const COLORS = ["#6366f1", "#8b5cf6", "#06b6d4", "#10b981", "#f59e0b", "#ef4444", "#ec4899", "#84cc16"];

export default function AnalyticsPage() {
  const [days, setDays] = useState(30);

  const { data: overview } = useQuery({
    queryKey: ["analytics-overview"],
    queryFn: () => analyticsApi.overview().then((r) => r.data),
  });

  const { data: volumeData } = useQuery({
    queryKey: ["case-volume", days],
    queryFn: () => analyticsApi.caseVolume(days).then((r) => r.data?.data ?? []),
  });

  const { data: sentimentData } = useQuery({
    queryKey: ["sentiment-trend", days],
    queryFn: () => analyticsApi.sentimentTrend(days).then((r) => r.data?.data ?? []),
  });

  const { data: categoryData } = useQuery({
    queryKey: ["category-breakdown"],
    queryFn: () => analyticsApi.categoryBreakdown().then((r) => r.data?.data ?? []),
  });

  const { data: statusData } = useQuery({
    queryKey: ["status-breakdown"],
    queryFn: () => analyticsApi.statusBreakdown().then((r) => r.data?.data ?? []),
  });

  const { data: agentPerformance } = useQuery({
    queryKey: ["agent-performance"],
    queryFn: () => analyticsApi.agentPerformance().then((r) => r.data?.data ?? []),
  });

  const { data: slaCompliance } = useQuery({
    queryKey: ["sla-compliance"],
    queryFn: () => analyticsApi.slaCompliance().then((r) => r.data?.data ?? []),
  });

  const tooltipStyle = { background: "rgba(15, 23, 42, 0.9)", border: "1px solid rgba(255, 255, 255, 0.1)", borderRadius: "12px", color: "#fff" };

  return (
    <div className="animate-fade-in pb-10">
      <TopBar title="Advanced Analytics" subtitle="Deep dive into your customer support metrics" />

      <div className="p-6 space-y-6">
        
        {/* Controls */}
        <div className="flex justify-between items-center bg-white dark:bg-slate-900 p-4 rounded-2xl border border-slate-200 dark:border-slate-800 shadow-sm">
          <h2 className="text-lg font-semibold text-slate-900 dark:text-white">Reporting Overview</h2>
          <div className="flex items-center gap-3">
            <span className="text-sm font-medium text-slate-500">Time Range:</span>
            <select 
              value={days} 
              onChange={(e) => setDays(Number(e.target.value))}
              className="input-field !py-2 !w-32 bg-slate-50 dark:bg-slate-800"
            >
              <option value={7}>Last 7 Days</option>
              <option value={14}>Last 14 Days</option>
              <option value={30}>Last 30 Days</option>
              <option value={90}>Last 90 Days</option>
            </select>
          </div>
        </div>

        {/* KPIs */}
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
          <div className="card-hover">
            <p className="text-xs font-bold uppercase tracking-wider text-slate-500 mb-2">Total Cases</p>
            <p className="text-4xl font-extrabold text-slate-900 dark:text-white">{overview?.total_cases ?? "—"}</p>
          </div>
          <div className="card-hover">
            <p className="text-xs font-bold uppercase tracking-wider text-slate-500 mb-2">Avg Resolution Time</p>
            <p className="text-4xl font-extrabold text-slate-900 dark:text-white">{overview?.avg_resolution_hours ? `${overview.avg_resolution_hours}h` : "—"}</p>
          </div>
          <div className="card-hover">
            <p className="text-xs font-bold uppercase tracking-wider text-slate-500 mb-2">Open Cases</p>
            <p className="text-4xl font-extrabold text-slate-900 dark:text-white">{overview?.open_cases ?? "—"}</p>
          </div>
          <div className="card-hover">
            <p className="text-xs font-bold uppercase tracking-wider text-slate-500 mb-2">Escalated</p>
            <p className="text-4xl font-extrabold text-slate-900 dark:text-white">{overview?.escalated_cases ?? "—"}</p>
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Category Breakdown */}
          <div className="card">
            <h3 className="text-base font-semibold text-slate-900 dark:text-white mb-4">Category Breakdown</h3>
            <ResponsiveContainer width="100%" height={280}>
              <PieChart>
                <Pie data={categoryData} cx="50%" cy="50%" innerRadius={70} outerRadius={100} dataKey="total" nameKey="category" paddingAngle={2}>
                  {categoryData?.map((_: any, i: number) => <Cell key={i} fill={COLORS[i % COLORS.length]} />)}
                </Pie>
                <Tooltip contentStyle={tooltipStyle} />
                <Legend formatter={(v) => <span className="text-sm text-slate-600 dark:text-slate-300 capitalize">{v?.replace("_", " ")}</span>} />
              </PieChart>
            </ResponsiveContainer>
          </div>

          {/* Status Breakdown */}
          <div className="card">
            <h3 className="text-base font-semibold text-slate-900 dark:text-white mb-4">Current Status</h3>
            <ResponsiveContainer width="100%" height={280}>
              <PieChart>
                <Pie data={statusData} cx="50%" cy="50%" innerRadius={70} outerRadius={100} dataKey="total" nameKey="status" paddingAngle={2}>
                  {statusData?.map((_: any, i: number) => <Cell key={i} fill={COLORS[(i+2) % COLORS.length]} />)}
                </Pie>
                <Tooltip contentStyle={tooltipStyle} />
                <Legend formatter={(v) => <span className="text-sm text-slate-600 dark:text-slate-300 capitalize">{v?.replace("_", " ")}</span>} />
              </PieChart>
            </ResponsiveContainer>
          </div>
          
          {/* Case Volume Trend */}
          <div className="card">
            <h3 className="text-base font-semibold text-slate-900 dark:text-white mb-4">Volume Trend ({days} Days)</h3>
            <ResponsiveContainer width="100%" height={250}>
              <AreaChart data={volumeData}>
                <defs>
                  <linearGradient id="colorTotal" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#8b5cf6" stopOpacity={0.3}/>
                    <stop offset="95%" stopColor="#8b5cf6" stopOpacity={0}/>
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" strokeOpacity={0.1} />
                <XAxis dataKey="day" tick={{ fontSize: 11 }} tickFormatter={(v) => format(new Date(v), "MMM d")} />
                <YAxis tick={{ fontSize: 11 }} />
                <Tooltip contentStyle={tooltipStyle} />
                <Area type="monotone" dataKey="total" stroke="#8b5cf6" fillOpacity={1} fill="url(#colorTotal)" name="Cases" />
              </AreaChart>
            </ResponsiveContainer>
          </div>

          {/* Sentiment Trend */}
          <div className="card">
            <h3 className="text-base font-semibold text-slate-900 dark:text-white mb-4">Sentiment Trend ({days} Days)</h3>
            <ResponsiveContainer width="100%" height={250}>
              <BarChart data={sentimentData}>
                <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" strokeOpacity={0.1} />
                <XAxis dataKey="day" tick={{ fontSize: 11 }} tickFormatter={(v) => format(new Date(v), "MMM d")} />
                <YAxis tick={{ fontSize: 11 }} />
                <Tooltip contentStyle={tooltipStyle} />
                <Legend />
                <Bar dataKey="positive" stackId="a" fill="#10b981" />
                <Bar dataKey="neutral" stackId="a" fill="#6366f1" />
                <Bar dataKey="negative" stackId="a" fill="#ef4444" />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Agent Performance Table */}
        <div className="card p-0 overflow-hidden mt-6">
          <div className="p-5 border-b border-slate-200 dark:border-slate-800">
            <h3 className="text-base font-semibold text-slate-900 dark:text-white">Agent Performance</h3>
          </div>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-slate-200 dark:border-slate-800 bg-slate-50 dark:bg-slate-900/50">
                  <th className="text-left px-5 py-3 text-xs font-semibold text-slate-500 dark:text-slate-400 uppercase">Agent</th>
                  <th className="text-left px-5 py-3 text-xs font-semibold text-slate-500 dark:text-slate-400 uppercase">Resolved</th>
                  <th className="text-left px-5 py-3 text-xs font-semibold text-slate-500 dark:text-slate-400 uppercase">Avg Resolution Time</th>
                  <th className="text-left px-5 py-3 text-xs font-semibold text-slate-500 dark:text-slate-400 uppercase">CSAT / Sentiment</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-200 dark:divide-slate-800/50">
                {agentPerformance?.length === 0 && (
                  <tr><td colSpan={4} className="py-8 text-center text-slate-500">No performance data available</td></tr>
                )}
                {agentPerformance?.map((agent: any) => (
                  <tr key={agent.agent_id} className="hover:bg-slate-50 dark:hover:bg-slate-800/30">
                    <td className="px-5 py-3">
                      <p className="font-medium text-slate-900 dark:text-white">{agent.full_name}</p>
                    </td>
                    <td className="px-5 py-3 text-slate-600 dark:text-slate-300">{agent.resolved_cases} cases</td>
                    <td className="px-5 py-3 text-slate-600 dark:text-slate-300">{agent.avg_resolution_hours ? `${agent.avg_resolution_hours.toFixed(1)} hrs` : "—"}</td>
                    <td className="px-5 py-3">
                      <div className="flex items-center gap-2">
                        <div className="w-full bg-slate-200 dark:bg-slate-700 rounded-full h-2">
                          <div className="bg-emerald-500 h-2 rounded-full" style={{ width: `${Math.min((agent.positive_sentiment_ratio || 0) * 100, 100)}%` }}></div>
                        </div>
                        <span className="text-xs text-slate-500">{(agent.positive_sentiment_ratio * 100).toFixed(0)}%</span>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>

        {/* SLA Compliance */}
        <div className="card mt-6">
          <h3 className="text-base font-semibold text-slate-900 dark:text-white mb-4">SLA Compliance by Priority</h3>
          <ResponsiveContainer width="100%" height={250}>
            <BarChart data={slaCompliance} layout="vertical">
              <CartesianGrid strokeDasharray="3 3" horizontal={false} stroke="#e2e8f0" strokeOpacity={0.1} />
              <XAxis type="number" tick={{ fontSize: 11 }} />
              <YAxis dataKey="priority" type="category" tick={{ fontSize: 11 }} width={100} />
              <Tooltip contentStyle={tooltipStyle} />
              <Legend />
              <Bar dataKey="within_sla" name="Within SLA" stackId="a" fill="#10b981" />
              <Bar dataKey="breached_sla" name="Breached SLA" stackId="a" fill="#ef4444" />
            </BarChart>
          </ResponsiveContainer>
        </div>

      </div>
    </div>
  );
}
