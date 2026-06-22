"use client";

import { useEffect, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { useDashboardStore } from "@/lib/store";
import { formatUptime } from "@/lib/utils";
import { Header } from "@/components/shared/header";
import { ToastContainer } from "@/components/ui/toast";
import { LiveAgents } from "./live-agents";
import { QueueHealth } from "./queue-health";
import { NewsThroughput } from "./news-throughput";
import { VideoProduction } from "./video-production";
import { RevenuePanel } from "./revenue-panel";
import { PipelineControl } from "./pipeline-control";
import { ScriptsPanel } from "./scripts-panel";
import { ActivityLog } from "./activity-log";
import { SettingsModal } from "./settings-modal";
import { Radio } from "lucide-react";

export function DashboardClient() {
  const { setScripts, updateStats, setApiOnline, addLog, isApiOnline } = useDashboardStore();
  const [settingsOpen, setSettingsOpen] = useState(false);

  const { data: health } = useQuery({
    queryKey: ["health"],
    queryFn: api.health,
    refetchInterval: 5000,
  });

  const { data: scripts } = useQuery({
    queryKey: ["scripts"],
    queryFn: () => api.scripts(20),
    refetchInterval: 10000,
  });

  useEffect(() => {
    if (health) {
      updateStats({
        uptime: formatUptime(health.uptime_seconds),
        activeJobs: health.active_jobs,
      });
      setApiOnline(true);
    }
  }, [health]);

  useEffect(() => {
    if (scripts) {
      setScripts(scripts);
      updateStats({ scriptsGenerated: scripts.length });
    }
  }, [scripts]);

  useEffect(() => {
    addLog("info", "A.N.N. Control Center initialized");
    addLog("ok", "All systems nominal — awaiting commands");
  }, []);

  return (
    <div className="flex min-h-screen flex-col bg-[#05050a]">
      <Header />

      {/* Control Center Title Bar */}
      <div className="border-b border-white/5 bg-[#080810]/80">
        <div className="mx-auto flex max-w-[1400px] items-center justify-between px-4 py-3">
          <div className="flex items-center gap-3">
            <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-gradient-to-br from-indigo-500 to-cyan-500">
              <Radio className="h-4 w-4 text-white" />
            </div>
            <div>
              <h1 className="text-sm font-bold tracking-tight">A.N.N. Control Center</h1>
              <p className="text-[10px] text-muted">Autonomous News Network Command Dashboard</p>
            </div>
          </div>
          <div className="flex items-center gap-3">
            <div className="flex items-center gap-1.5 rounded-full border border-white/10 bg-white/5 px-3 py-1">
              <span className={`h-2 w-2 rounded-full ${isApiOnline ? "bg-emerald-500 live-dot" : "bg-red-500"}`} />
              <span className="text-[10px] font-medium">{isApiOnline ? "SYSTEMS ONLINE" : "OFFLINE"}</span>
            </div>
            <button
              onClick={() => setSettingsOpen(true)}
              className="rounded-lg border border-white/10 bg-white/5 px-3 py-1.5 text-xs text-muted hover:bg-white/10 transition-colors"
            >
              Settings
            </button>
          </div>
        </div>
      </div>

      <main className="mx-auto w-full max-w-[1400px] flex-1 space-y-4 p-4">
        {/* Row 1: Live Agents (full width) */}
        <LiveAgents />

        {/* Row 2: Queue Health + News Throughput */}
        <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
          <QueueHealth />
          <NewsThroughput />
        </div>

        {/* Row 3: Video Production + Revenue */}
        <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
          <VideoProduction />
          <RevenuePanel />
        </div>

        {/* Row 4: Pipeline Control */}
        <PipelineControl />

        {/* Row 5: Scripts + Activity Log */}
        <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
          <ScriptsPanel />
          <ActivityLog />
        </div>
      </main>

      <SettingsModal open={settingsOpen} onClose={() => setSettingsOpen(false)} />
      <ToastContainer />
    </div>
  );
}
