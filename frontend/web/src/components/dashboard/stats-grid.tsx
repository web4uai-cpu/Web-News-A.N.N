"use client";

import { motion } from "framer-motion";
import { useDashboardStore } from "@/lib/store";
import { FileText, Newspaper, Zap, Clock } from "lucide-react";

const stats = [
  { key: "scriptsGenerated", label: "Scripts Generated", sub: "Ready for broadcast", Icon: FileText },
  { key: "articlesProcessed", label: "Articles Processed", sub: "Across all sources", Icon: Newspaper },
  { key: "activeJobs", label: "Active Jobs", sub: "Pipeline runs", Icon: Zap },
  { key: "uptime", label: "Uptime", sub: "Since last restart", Icon: Clock },
] as const;

export function StatsGrid() {
  const s = useDashboardStore((state) => state.stats);

  return (
    <div className="grid grid-cols-2 gap-4 lg:grid-cols-4">
      {stats.map(({ key, label, sub, Icon }, i) => (
        <motion.div
          key={key}
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: i * 0.1 }}
          className="rounded-xl border border-white/5 bg-white/[0.02] p-4 backdrop-blur-sm"
        >
          <div className="flex items-center gap-2 text-xs text-muted">
            <Icon className="h-3.5 w-3.5" />
            {label}
          </div>
          <div className="mt-2 text-2xl font-bold">{s[key]}</div>
          <div className="mt-1 text-xs text-muted">{sub}</div>
        </motion.div>
      ))}
    </div>
  );
}
