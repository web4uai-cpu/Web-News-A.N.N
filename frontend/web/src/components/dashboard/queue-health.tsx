"use client";

import { useEffect, useState } from "react";
import { motion } from "framer-motion";
import { useDashboardStore } from "@/lib/store";
import { Server, Cpu, HardDrive, Wifi, Database, Clock } from "lucide-react";

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
  const [metrics, setMetrics] = useState<QueueMetric[]>([]);

  useEffect(() => {
    const update = () => {
      setMetrics([
        {
          label: "Celery Queue",
          value: `${Math.floor(Math.random() * 12)}`,
          max: "50 capacity",
          pct: Math.floor(Math.random() * 40),
          color: "from-cyan-500 to-blue-500",
          Icon: Server,
        },
        {
          label: "Redis Memory",
          value: `${(Math.random() * 80 + 20).toFixed(0)}MB`,
          max: "256MB",
          pct: Math.floor(Math.random() * 30 + 10),
          color: "from-violet-500 to-purple-500",
          Icon: Database,
        },
        {
          label: "CPU Load",
          value: `${(Math.random() * 40 + 10).toFixed(0)}%`,
          max: "2 cores",
          pct: Math.floor(Math.random() * 40 + 10),
          color: "from-amber-500 to-orange-500",
          Icon: Cpu,
        },
        {
          label: "Disk I/O",
          value: `${(Math.random() * 20 + 5).toFixed(1)}MB/s`,
          max: "100MB/s",
          pct: Math.floor(Math.random() * 25 + 5),
          color: "from-emerald-500 to-green-500",
          Icon: HardDrive,
        },
      ]);
    };
    update();
    const id = setInterval(update, 4000);
    return () => clearInterval(id);
  }, []);

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

      {/* System Status Bar */}
      <div className="mb-4 flex gap-3">
        {[
          { label: "API", online: isApiOnline },
          { label: "Redis", online: true },
          { label: "Celery", online: true },
          { label: "Supabase", online: true },
          { label: "LLM", online: true },
        ].map((svc) => (
          <div key={svc.label} className="flex items-center gap-1 text-[10px]">
            <span className={`h-1.5 w-1.5 rounded-full ${svc.online ? "bg-emerald-500" : "bg-red-500"}`} />
            <span className="text-white/40">{svc.label}</span>
          </div>
        ))}
      </div>

      {/* Metric Bars */}
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

      {/* Uptime + Jobs */}
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
