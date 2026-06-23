"use client";

import { motion } from "framer-motion";
import { useDashboardStore } from "@/lib/store";
import { Server, Cpu, HardDrive, Wifi, Database, Clock } from "lucide-react";
import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api";

interface QueueMetric {
  label: string;
  value: string;
  max: string;
  pct: number;
  color: string;
  Icon: typeof Server;
}

export function QueueHealth() {
  const { isApiOnline, stats } = useDashboardStore();

  const { data: system } = useQuery({
    queryKey: ["dashboard-system"],
    queryFn: () => api.dashboardSystem(),
    refetchInterval: 5000,
  });

  const metrics: QueueMetric[] = system
    ? [
        {
          label: "CPU Load",
          value: `${system.cpu_percent.toFixed(0)}%`,
          max: "100%",
          pct: Math.min(system.cpu_percent, 100),
          color: "from-amber-500 to-orange-500",
          Icon: Cpu,
        },
        {
          label: "Memory",
          value: `${system.memory_used_mb.toFixed(0)}MB`,
          max: `${system.memory_percent.toFixed(0)}%`,
          pct: Math.min(system.memory_percent, 100),
          color: "from-violet-500 to-purple-500",
          Icon: Database,
        },
        {
          label: "Disk Usage",
          value: `${system.disk_usage_percent.toFixed(0)}%`,
          max: "100%",
          pct: Math.min(system.disk_usage_percent, 100),
          color: "from-emerald-500 to-green-500",
          Icon: HardDrive,
        },
        {
          label: "Scripts in Memory",
          value: `${system.scripts_in_memory}`,
          max: "cache",
          pct: Math.min(system.scripts_in_memory * 2, 100),
          color: "from-cyan-500 to-blue-500",
          Icon: Server,
        },
      ]
    : [];

  const redisOnline = system ? system.redis_status === "connected" : true;
  const celeryOnline = system ? system.celery_status === "connected" : true;

  return (
    <div className="rounded-xl border border-white/5 bg-white/[0.02] p-5 backdrop-blur-sm">
      <div className="mb-4 flex items-center justify-between">
        <h2 className="flex items-center gap-2 text-sm font-semibold">
          <Server className="h-4 w-4 text-violet-400" />
          Queue Health
        </h2>
        <div className="flex items-center gap-1.5">
          <span className={`h-2 w-2 rounded-full ${isApiOnline ? "bg-emerald-500 live-dot" : "bg-red-500"}`} />
          <span className={`text-[10px] font-medium ${isApiOnline ? "text-emerald-400" : "text-red-400"}`}>
            {isApiOnline ? "ALL SYSTEMS NOMINAL" : "OFFLINE"}
          </span>
        </div>
      </div>

      <div className="mb-4 flex gap-3">
        {[
          { label: "API", online: isApiOnline },
          { label: "Redis", online: redisOnline },
          { label: "Celery", online: celeryOnline },
          { label: "Supabase", online: true },
          { label: "LLM", online: true },
        ].map((svc) => (
          <div key={svc.label} className="flex items-center gap-1 text-[10px]">
            <span className={`h-1.5 w-1.5 rounded-full ${svc.online ? "bg-emerald-500" : "bg-red-500"}`} />
            <span className="text-white/40">{svc.label}</span>
          </div>
        ))}
      </div>

      <div className="space-y-3">
        {metrics.map((m) => (
          <div key={m.label}>
            <div className="mb-1 flex items-center justify-between">
              <div className="flex items-center gap-1.5 text-xs text-muted">
                <m.Icon className="h-3 w-3" />
                {m.label}
              </div>
              <div className="text-xs font-medium">{m.value} <span className="text-white/20">/ {m.max}</span></div>
            </div>
            <div className="h-1.5 w-full overflow-hidden rounded-full bg-white/5">
              <motion.div
                className={`h-full rounded-full bg-gradient-to-r ${m.color}`}
                initial={{ width: 0 }}
                animate={{ width: `${m.pct}%` }}
                transition={{ duration: 0.8, ease: "easeOut" }}
              />
            </div>
          </div>
        ))}
      </div>

      <div className="mt-4 flex gap-4 border-t border-white/5 pt-3">
        <div className="flex items-center gap-1.5 text-[10px] text-muted">
          <Clock className="h-3 w-3" />
          Uptime: <span className="font-medium text-white">{stats.uptime}</span>
        </div>
        <div className="flex items-center gap-1.5 text-[10px] text-muted">
          <Wifi className="h-3 w-3" />
          Active Jobs: <span className="font-medium text-white">{stats.activeJobs}</span>
        </div>
      </div>
    </div>
  );
}
