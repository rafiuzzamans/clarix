"use client";

import { useQuery } from "@tanstack/react-query";
import { analyticsApi } from "@/lib/api";
import TopBar from "@/components/layout/TopBar";
import {
  AreaChart, Area, BarChart, Bar, PieChart, Pie, Cell,
  XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend,
} from "recharts";
import { format } from "date-fns";
import { TrendingUp, ShieldCheck, Users, Clock } from "lucide-react";

const COLORS = ["#ef4444", "#f59e0b", "#6366f1", "#10b981"];
const PIE_COLORS = ["#6366f1","#8b5cf6","#06b6d4","#10b981","#f59e0b","#ef4444","#ec4899","#84cc16"];

export default function AnalyticsPage() {
  const { data: overview }     = useQuery({ queryKey: ["analytics-overview"],  queryFn: () => analyticsApi.overview().then(r=>r.data) });
  const { data: volumeRaw }    = useQuery({ queryKey: ["case-volume-30"],       queryFn: () => analyticsApi.caseVolume(30).then(r=>r.data?.data ?? []) });
  const { data: sentimentRaw } = useQuery({ queryKey: ["sentiment-30"],         queryFn: () => analyticsApi.sentimentTrend(30).then(r=>r.data?.data ?? []) });
  const { data: priorityRaw }  = useQuery({ queryKey: ["priority-breakdown"],   queryFn: () => analyticsApi.priorityBreakdown().then(r=>r.data?.data ?? []) });
  const { data: categoryRaw }  = useQuery({ queryKey: ["category-breakdown"],   queryFn: () => analyticsApi.categoryBreakdown().then(r=>r.data?.data ?? []) });
  const { data: agentRaw }     = useQuery({ queryKey: ["agent-performance"],    queryFn: () => analyticsApi.agentPerformance().then(r=>r.data?.data ?? []) });
  const { data: sla }          = useQuery({ queryKey: ["sla-compliance"],       queryFn: () => analyticsApi.slaCompliance().then(r=>r.data) });

  const statCards = [
    { label: "Total Cases",        value: overview?.total_cases,             icon: TrendingUp,  color: "text-indigo-400" },
    { label: "Avg Resolution (h)", value: overview?.avg_resolution_hours,    icon: Clock,       color: "text-violet-400" },
    { label: "SLA Compliance",     value: sla?.compliance_pct ? `${sla.compliance_pct}%` : "—", icon: ShieldCheck, color: "text-emerald-400" },
    { label: "Escalation Rate",    value: overview?.total_cases
        ? `${Math.round((overview.escalated_cases / overview.total_cases) * 100)}%` : "—",
      icon: Users, color: "text-orange-400" },
  ];

  return (
    <div className="animate-fade-in">
      <TopBar title="Analytics & Reports" subtitle="Platform-wide performance metrics" />

      <div className="p-6 space-y-6">

        {/* Stat row */}
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
          {statCards.map(({ label, value, icon: Icon, color }) => (
            <div key={label} className="card-hover">
              <div className="flex items-center gap-2 mb-2">
                <Icon className={`w-4 h-4 ${color}`} />
                <span className="text-xs text-slate-400 font-medium">{label}</span>
              </div>
              <p className="text-3xl font-bold text-white">{value ?? "—"}</p>
            </div>
          ))}
        </div>

        {/* Volume & Sentiment */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <div className="card">
            <h3 className="text-base font-semibold text-white mb-4">Case Volume — 30 Days</h3>
            <ResponsiveContainer width="100%" height={240}>
              <AreaChart data={volumeRaw as any[]}>
                <defs>
                  <linearGradient id="g1" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%"  stopColor="#6366f1" stopOpacity={0.3}/>
                    <stop offset="95%" stopColor="#6366f1" stopOpacity={0}/>
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="#1e293b"/>
                <XAxis dataKey="day" tick={{fill:"#64748b",fontSize:10}} tickFormatter={v=>format(new Date(v),"MMM d")}/>
                <YAxis tick={{fill:"#64748b",fontSize:10}}/>
                <Tooltip contentStyle={{background:"#0f172a",border:"1px solid #1e293b",borderRadius:"12px"}}/>
                <Area type="monotone" dataKey="total" stroke="#6366f1" fill="url(#g1)" strokeWidth={2} name="Total"/>
                <Area type="monotone" dataKey="resolved" stroke="#10b981" fill="none" strokeWidth={2} strokeDasharray="4 4" name="Resolved"/>
                <Area type="monotone" dataKey="escalated" stroke="#ef4444" fill="none" strokeWidth={1.5} strokeDasharray="4 4" name="Escalated"/>
              </AreaChart>
            </ResponsiveContainer>
          </div>

          <div className="card">
            <h3 className="text-base font-semibold text-white mb-4">Sentiment Distribution — 30 Days</h3>
            <ResponsiveContainer width="100%" height={240}>
              <BarChart data={sentimentRaw as any[]}>
                <CartesianGrid strokeDasharray="3 3" stroke="#1e293b"/>
                <XAxis dataKey="day" tick={{fill:"#64748b",fontSize:10}} tickFormatter={v=>format(new Date(v),"MMM d")}/>
                <YAxis tick={{fill:"#64748b",fontSize:10}}/>
                <Tooltip contentStyle={{background:"#0f172a",border:"1px solid #1e293b",borderRadius:"12px"}}/>
                <Legend/>
                <Bar dataKey="positive" fill="#10b981" stackId="a" name="Positive" radius={[3,3,0,0]}/>
                <Bar dataKey="neutral"  fill="#6366f1" stackId="a" name="Neutral"/>
                <Bar dataKey="negative" fill="#ef4444" stackId="a" name="Negative" radius={[3,3,0,0]}/>
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Priority + Category */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <div className="card">
            <h3 className="text-base font-semibold text-white mb-4">Priority Breakdown</h3>
            <ResponsiveContainer width="100%" height={220}>
              <PieChart>
                <Pie data={priorityRaw as any[]} cx="50%" cy="50%" innerRadius={60} outerRadius={90}
                     dataKey="total" nameKey="priority" paddingAngle={3}>
                  {(priorityRaw as any[] ?? []).map((_:any, i:number) => (
                    <Cell key={i} fill={COLORS[i % COLORS.length]}/>
                  ))}
                </Pie>
                <Tooltip contentStyle={{background:"#0f172a",border:"1px solid #1e293b",borderRadius:"12px"}}/>
                <Legend formatter={(v) => <span className="text-xs text-slate-400 capitalize">{v}</span>}/>
              </PieChart>
            </ResponsiveContainer>
          </div>

          <div className="card">
            <h3 className="text-base font-semibold text-white mb-4">Cases by Category</h3>
            <ResponsiveContainer width="100%" height={220}>
              <BarChart data={categoryRaw as any[]} layout="vertical">
                <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" horizontal={false}/>
                <XAxis type="number" tick={{fill:"#64748b",fontSize:10}}/>
                <YAxis dataKey="category" type="category" tick={{fill:"#64748b",fontSize:10}} width={110}
                       tickFormatter={v=>v?.replace("_"," ")}/>
                <Tooltip contentStyle={{background:"#0f172a",border:"1px solid #1e293b",borderRadius:"12px"}}/>
                <Bar dataKey="total" fill="#6366f1" radius={[0,4,4,0]}/>
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Agent performance */}
        <div className="card">
          <h3 className="text-base font-semibold text-white mb-4">Agent Performance</h3>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-slate-800">
                  {["Agent","Department","Assigned","Resolved","Escalated","Avg Resolution (h)"].map(h=>(
                    <th key={h} className="text-left px-4 py-2 text-xs font-semibold text-slate-400 uppercase tracking-wider">{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/50">
                {(agentRaw as any[] ?? []).map((a: any) => (
                  <tr key={a.agent_id} className="hover:bg-slate-800/20 transition-colors">
                    <td className="px-4 py-3 font-medium text-white">{a.full_name}</td>
                    <td className="px-4 py-3 text-slate-400">{a.department || "—"}</td>
                    <td className="px-4 py-3 text-slate-300">{a.assigned_cases}</td>
                    <td className="px-4 py-3 text-emerald-400 font-semibold">{a.resolved_cases}</td>
                    <td className="px-4 py-3 text-orange-400">{a.escalated_cases}</td>
                    <td className="px-4 py-3 text-slate-300">{a.avg_resolution_hours ?? "—"}</td>
                  </tr>
                ))}
                {!(agentRaw as any[])?.length && (
                  <tr><td colSpan={6} className="px-4 py-8 text-center text-slate-500">No agent data yet</td></tr>
                )}
              </tbody>
            </table>
          </div>
        </div>

        {/* SLA Compliance */}
        {sla && (
          <div className="card">
            <h3 className="text-base font-semibold text-white mb-4 flex items-center gap-2">
              <ShieldCheck className="w-4 h-4 text-emerald-400"/> SLA Compliance Summary
            </h3>
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
              {[
                { label: "Total with SLA",  value: sla.total,        color: "text-white" },
                { label: "Within SLA",      value: sla.within_sla,   color: "text-emerald-400" },
                { label: "Breached SLA",    value: sla.breached_sla, color: "text-red-400" },
                { label: "Compliance",      value: sla.compliance_pct ? `${sla.compliance_pct}%` : "—", color: "text-indigo-400" },
              ].map(({ label, value, color }) => (
                <div key={label} className="bg-slate-800/50 rounded-xl p-4 border border-slate-700/50">
                  <p className="text-xs text-slate-500 mb-1">{label}</p>
                  <p className={`text-2xl font-bold ${color}`}>{value}</p>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
