"use client";

import { useQuery, useMutation } from "@tanstack/react-query";
import { aiApi } from "@/lib/api";
import TopBar from "@/components/layout/TopBar";
import { Bot, Play, RefreshCw, Server, Database, Shield } from "lucide-react";
import toast from "react-hot-toast";
import Link from "next/link";

const SERVICES = [
  { name: "Auth Service",        port: 8001, path: "/api/auth/health"  },
  { name: "User Service",        port: 8002, path: "/api/users/health"  },
  { name: "Case Service",        port: 8003, path: "/api/cases/health"  },
  { name: "AI Service",          port: 8004, path: "/api/ai/health"     },
  { name: "Chatbot Service",     port: 8005, path: "/api/chatbot/health" },
  { name: "Automation Service",  port: 8006, path: "/api/automation/health" },
  { name: "Notification Service",port: 8007, path: "/api/notifications/health" },
  { name: "Analytics Service",   port: 8008, path: "/api/analytics/health" },
  { name: "File Service",        port: 8009, path: "/api/files/health"  },
  { name: "Audit Service",       port: 8010, path: "/api/audit/health"  },
];

export default function AdminPage() {
  const { data: aiStatus, refetch } = useQuery({
    queryKey: ["ai-status-admin"],
    queryFn: () => aiApi.status().then(r=>r.data),
  });

  const trainMutation = useMutation({
    mutationFn: () => aiApi.train(),
    onSuccess: () => { toast.success("Models trained successfully!"); refetch(); },
    onError: () => toast.error("Training failed"),
  });

  return (
    <div className="animate-fade-in">
      <TopBar title="Admin Panel" subtitle="System administration and monitoring" />
      <div className="p-6 space-y-6">

        {/* AI Training */}
        <div className="card border-violet-500/30 bg-violet-950/10">
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center gap-3">
              <Bot className="w-5 h-5 text-violet-400" />
              <div>
                <h3 className="text-base font-semibold text-white">AI Model Management</h3>
                <p className="text-xs text-slate-400">Train and monitor classification models</p>
              </div>
            </div>
            <button
              id="train-models-btn"
              onClick={() => trainMutation.mutate()}
              disabled={trainMutation.isPending}
              className="btn-primary"
            >
              {trainMutation.isPending ? (
                <><RefreshCw className="w-4 h-4 animate-spin" /> Training...</>
              ) : (
                <><Play className="w-4 h-4" /> Train Models</>
              )}
            </button>
          </div>

          {aiStatus?.evaluation_report && (
            <div className="grid grid-cols-3 gap-4">
              {Object.entries(aiStatus.evaluation_report).map(([model, metrics]: any) => (
                <div key={model} className="bg-slate-800/60 rounded-xl p-4 border border-slate-700/50">
                  <p className="text-xs text-violet-400 font-semibold uppercase mb-3">{model}</p>
                  <div className="space-y-1.5">
                    <div className="flex justify-between text-sm">
                      <span className="text-slate-400">Accuracy</span>
                      <span className="font-bold text-white">{(metrics.accuracy*100).toFixed(1)}%</span>
                    </div>
                    <div className="flex justify-between text-sm">
                      <span className="text-slate-400">F1 Score</span>
                      <span className="font-bold text-violet-300">{(metrics.f1_weighted*100).toFixed(1)}%</span>
                    </div>
                    {/* Progress bar */}
                    <div className="w-full bg-slate-700 rounded-full h-1.5 mt-2">
                      <div className="bg-violet-500 h-1.5 rounded-full" style={{width:`${metrics.accuracy*100}%`}}/>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
          {!aiStatus?.models_loaded && (
            <p className="text-sm text-slate-400 bg-slate-800/50 rounded-xl p-4 border border-slate-700">
              ⚠️ Models not trained yet. Click "Train Models" to run the training pipeline.
              This will generate synthetic data and train the category, priority, and sentiment classifiers.
            </p>
          )}
        </div>

        {/* Service health */}
        <div className="card">
          <div className="flex items-center gap-2 mb-4">
            <Server className="w-4 h-4 text-slate-400" />
            <h3 className="text-base font-semibold text-white">Service Registry</h3>
          </div>
          <div className="grid grid-cols-2 lg:grid-cols-5 gap-3">
            {SERVICES.map((svc) => (
              <div key={svc.name} className="bg-slate-800/50 rounded-xl p-3 border border-slate-700/50">
                <p className="text-xs font-medium text-white truncate">{svc.name}</p>
                <p className="text-xs text-slate-500 mt-0.5">:{svc.port}</p>
                <div className="flex items-center gap-1 mt-2">
                  <div className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse" />
                  <span className="text-xs text-emerald-400">Running</span>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Quick links */}
        <div className="card">
          <h3 className="text-base font-semibold text-white mb-4 flex items-center gap-2">
            <Shield className="w-4 h-4 text-slate-400" /> Quick Links
          </h3>
          <div className="flex flex-wrap gap-3">
            {[
              { label: "MailHog (Email UI)", href: "http://localhost:8025", color: "text-cyan-400" },
              { label: "Auth Service Docs",  href: "http://localhost:8001/docs", color: "text-indigo-400" },
              { label: "Case Service Docs",  href: "http://localhost:8003/docs", color: "text-violet-400" },
              { label: "AI Service Docs",    href: "http://localhost:8004/docs", color: "text-purple-400" },
              { label: "Analytics Docs",     href: "http://localhost:8008/docs", color: "text-emerald-400" },
            ].map(({ label, href, color }) => (
              <a key={label} href={href} target="_blank" rel="noopener noreferrer"
                 className={`text-sm px-4 py-2 bg-slate-800 border border-slate-700 rounded-xl hover:bg-slate-700 transition-all ${color}`}>
                {label} ↗
              </a>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
