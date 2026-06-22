"use client";

import { useEffect, useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Bot, CheckCircle, Loader2, AlertTriangle, Pause } from "lucide-react";

type AgentStatus = "idle" | "running" | "completed" | "error";

interface AgentState {
  name: string;
  shortName: string;
  status: AgentStatus;
  lastRun: string;
  tasksCompleted: number;
  avgLatency: string;
}

const INITIAL_AGENTS: AgentState[] = [
  { name: "Discovery Agent", shortName: "DSC", status: "idle", lastRun: "--", tasksCompleted: 0, avgLatency: "--" },
  { name: "Fact Extractor", shortName: "FCT", status: "idle", lastRun: "--", tasksCompleted: 0, avgLatency: "--" },
  { name: "Scriptwriter", shortName: "SCR", status: "idle", lastRun: "--", tasksCompleted: 0, avgLatency: "--" },
  { name: "Critic Agent", shortName: "CRT", status: "idle", lastRun: "--", tasksCompleted: 0, avgLatency: "--" },
  { name: "Headline Gen", shortName: "HDL", status: "idle", lastRun: "--", tasksCompleted: 0, avgLatency: "--" },
  { name: "Translator", shortName: "TRN", status: "idle", lastRun: "--", tasksCompleted: 0, avgLatency: "--" },
  { name: "SEO Agent", shortName: "SEO", status: "idle", lastRun: "--", tasksCompleted: 0, avgLatency: "--" },
  { name: "Avatar Producer", shortName: "AVT", status: "idle", lastRun: "--", tasksCompleted: 0, avgLatency: "--" },
  { name: "Publisher", shortName: "PUB", status: "idle", lastRun: "--", tasksCompleted: 0, avgLatency: "--" },
  { name: "Legal Agent", shortName: "LGL", status: "idle", lastRun: "--", tasksCompleted: 0, avgLatency: "--" },
];

const STATUS_CONFIG: Record<AgentStatus, { color: string; bg: string; Icon: typeof Bot }> = {
  idle: { color: "text-white/30", bg: "bg-white/5", Icon: Pause },
  running: { color: "text-cyan-400", bg: "bg-cyan-500/10", Icon: Loader2 },
  completed: { color: "text-emerald-400", bg: "bg-emerald-500/10", Icon: CheckCircle },
  error: { color: "text-red-400", bg: "bg-red-500/10", Icon: AlertTriangle },
};

export function LiveAgents() {
  const [agents, setAgents] = useState(INITIAL_AGENTS);

  useEffect(() => {
    const latencies = ["1.2s", "2.4s", "3.1s", "0.8s", "1.5s", "4.2s", "0.9s", "12.3s", "1.8s", "2.0s"];
    const statuses: AgentStatus[] = ["idle", "running", "completed", "error"];

    const interval = setInterval(() => {
      setAgents((prev) =>
        prev.map((agent, i) => {
          const rand = Math.random();
          if (rand < 0.15) {
            const newStatus = statuses[Math.floor(Math.random() * 3)];
            return {
              ...agent,
              status: newStatus,
              lastRun: newStatus !== "idle" ? new Date().toLocaleTimeString("en-US", { hour12: false }) : agent.lastRun,
              tasksCompleted: newStatus === "completed" ? agent.tasksCompleted + 1 : agent.tasksCompleted,
              avgLatency: latencies[i],
            };
          }
          return agent;
        })
      );
    }, 2000);

    return () => clearInterval(interval);
  }, []);

  const running = agents.filter((a) => a.status === "running").length;
  const completed = agents.reduce((sum, a) => sum + a.tasksCompleted, 0);
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
          const cfg = STATUS_CONFIG[agent.status];
          return (
            <motion.div
              key={agent.shortName}
              layout
              className={`relative rounded-lg border border-white/5 ${cfg.bg} p-3 transition-colors`}
            >
              <div className="flex items-center justify-between">
                <span className="text-[10px] font-bold tracking-wider text-white/50">{agent.shortName}</span>
                <cfg.Icon className={`h-3 w-3 ${cfg.color} ${agent.status === "running" ? "animate-spin" : ""}`} />
              </div>
              <div className={`mt-1 text-xs font-medium truncate ${cfg.color}`}>{agent.name}</div>
              <div className="mt-2 flex justify-between text-[9px] text-white/30">
                <span>{agent.avgLatency}</span>
                <span>{agent.tasksCompleted} done</span>
              </div>
              {agent.status === "running" && (
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
