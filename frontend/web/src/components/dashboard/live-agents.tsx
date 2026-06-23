"use client";

import { motion } from "framer-motion";
import { Bot, CheckCircle, Loader2, AlertTriangle, Pause } from "lucide-react";
import { useQuery } from "@tanstack/react-query";
import { api, AgentMetric } from "@/lib/api";

type AgentStatus = "idle" | "running" | "completed" | "error";

const FALLBACK_AGENTS: AgentMetric[] = [
  { name: "Discovery Agent", shortName: "DSC", tasks_completed: 0, avg_latency: "--", status: "idle", last_run: "--" },
  { name: "Fact Extractor", shortName: "FCT", tasks_completed: 0, avg_latency: "--", status: "idle", last_run: "--" },
  { name: "Scriptwriter", shortName: "SCR", tasks_completed: 0, avg_latency: "--", status: "idle", last_run: "--" },
  { name: "Critic Agent", shortName: "CRT", tasks_completed: 0, avg_latency: "--", status: "idle", last_run: "--" },
  { name: "Headline Gen", shortName: "HDL", tasks_completed: 0, avg_latency: "--", status: "idle", last_run: "--" },
  { name: "Translator", shortName: "TRN", tasks_completed: 0, avg_latency: "--", status: "idle", last_run: "--" },
  { name: "SEO Agent", shortName: "SEO", tasks_completed: 0, avg_latency: "--", status: "idle", last_run: "--" },
  { name: "Avatar Producer", shortName: "AVT", tasks_completed: 0, avg_latency: "--", status: "idle", last_run: "--" },
  { name: "Publisher", shortName: "PUB", tasks_completed: 0, avg_latency: "--", status: "idle", last_run: "--" },
  { name: "Legal Agent", shortName: "LGL", tasks_completed: 0, avg_latency: "--", status: "idle", last_run: "--" },
];

const STATUS_CONFIG: Record<AgentStatus, { color: string; bg: string; Icon: typeof Bot }> = {
  idle: { color: "text-white/30", bg: "bg-white/5", Icon: Pause },
  running: { color: "text-cyan-400", bg: "bg-cyan-500/10", Icon: Loader2 },
  completed: { color: "text-emerald-400", bg: "bg-emerald-500/10", Icon: CheckCircle },
  error: { color: "text-red-400", bg: "bg-red-500/10", Icon: AlertTriangle },
};

function generateShortName(name: string): string {
  return name
    .split(/\s+/)
    .map((w) => w.slice(0, 3).toUpperCase())
    .join("")
    .slice(0, 3);
}

export function LiveAgents() {
  const { data } = useQuery({
    queryKey: ["dashboard-agents"],
    queryFn: () => api.dashboardAgents(),
    refetchInterval: 5000,
  });

  const agents = data && data.length > 0 ? data : FALLBACK_AGENTS;

  const running = agents.filter((a) => a.status === "running").length;
  const completed = agents.reduce((sum, a) => sum + a.tasks_completed, 0);
  const errors = agents.filter((a) => a.status === "error").length;

  return (
    <div className="rounded-xl border border-white/5 bg-white/[0.02] p-5 backdrop-blur-sm">
      <div className="mb-4 flex items-center justify-between">
        <h2 className="flex items-center gap-2 text-sm font-semibold">
          <Bot className="h-4 w-4 text-cyan-400" />
          Live Agents
        </h2>
        <div className="flex gap-3 text-[10px]">
          <span className="text-cyan-400">{running} active</span>
          <span className="text-emerald-400">{completed} completed</span>
          {errors > 0 && <span className="text-red-400">{errors} errors</span>}
        </div>
      </div>

      <div className="grid grid-cols-2 gap-2 sm:grid-cols-5">
        {agents.map((agent) => {
          const status = (agent.status as AgentStatus) || "idle";
          const cfg = STATUS_CONFIG[status] || STATUS_CONFIG.idle;
          const shortName = agent.shortName || generateShortName(agent.name);
          return (
            <motion.div
              key={shortName}
              layout
              className={`relative rounded-lg border border-white/5 ${cfg.bg} p-3 transition-colors`}
            >
              <div className="flex items-center justify-between">
                <span className="text-[10px] font-bold tracking-wider text-white/50">{shortName}</span>
                <cfg.Icon className={`h-3 w-3 ${cfg.color} ${status === "running" ? "animate-spin" : ""}`} />
              </div>
              <div className={`mt-1 text-xs font-medium truncate ${cfg.color}`}>{agent.name}</div>
              <div className="mt-2 flex justify-between text-[9px] text-white/30">
                <span>{agent.avg_latency}</span>
                <span>{agent.tasks_completed} done</span>
              </div>
              {status === "running" && (
                <motion.div
                  className="absolute bottom-0 left-0 h-0.5 rounded-full bg-cyan-400"
                  initial={{ width: "0%" }}
                  animate={{ width: "100%" }}
                  transition={{ duration: 3, repeat: Infinity }}
                />
              )}
            </motion.div>
          );
        })}
      </div>
    </div>
  );
}
