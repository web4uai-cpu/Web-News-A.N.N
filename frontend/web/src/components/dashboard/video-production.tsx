"use client";

import { useEffect, useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Video, Mic, PlayCircle, CheckCircle, Loader2, Clock } from "lucide-react";

type JobStatus = "queued" | "tts" | "rendering" | "complete" | "failed";

interface VideoJob {
  id: string;
  headline: string;
  language: string;
  status: JobStatus;
  progress: number;
  duration: string;
  createdAt: string;
}

const STATUS_MAP: Record<JobStatus, { label: string; color: string; Icon: typeof Video }> = {
  queued: { label: "Queued", color: "text-white/40", Icon: Clock },
  tts: { label: "TTS Synthesis", color: "text-violet-400", Icon: Mic },
  rendering: { label: "Avatar Render", color: "text-cyan-400", Icon: Loader2 },
  complete: { label: "Complete", color: "text-emerald-400", Icon: CheckCircle },
  failed: { label: "Failed", color: "text-red-400", Icon: Video },
};

const DEMO_JOBS: VideoJob[] = [
  { id: "v1", headline: "AI Summit Reshapes Global Policy", language: "EN", status: "complete", progress: 100, duration: "1:24", createdAt: "14:32" },
  { id: "v2", headline: "Bitcoin Surges Past $90K Mark", language: "HI", status: "rendering", progress: 68, duration: "--", createdAt: "14:45" },
  { id: "v3", headline: "EU Climate Deal Signed in Brussels", language: "EN", status: "tts", progress: 35, duration: "--", createdAt: "14:51" },
  { id: "v4", headline: "SpaceX Launches Lunar Mission", language: "EN", status: "queued", progress: 0, duration: "--", createdAt: "14:58" },
];

export function VideoProduction() {
  const [jobs, setJobs] = useState(DEMO_JOBS);

  useEffect(() => {
    const interval = setInterval(() => {
      setJobs((prev) =>
        prev.map((job) => {
          if (job.status === "complete" || job.status === "failed") return job;
          const newProgress = Math.min(job.progress + Math.floor(Math.random() * 12 + 3), 100);
          let newStatus: JobStatus = job.status;
          if (newProgress >= 100) newStatus = "complete";
          else if (newProgress >= 60) newStatus = "rendering";
          else if (newProgress >= 20) newStatus = "tts";
          return {
            ...job,
            progress: newProgress,
            status: newStatus,
            duration: newStatus === "complete" ? `${Math.floor(Math.random() * 2)}:${String(Math.floor(Math.random() * 59)).padStart(2, "0")}` : "--",
          };
        })
      );
    }, 3000);
    return () => clearInterval(interval);
  }, []);

  const completed = jobs.filter((j) => j.status === "complete").length;
  const rendering = jobs.filter((j) => j.status !== "complete" && j.status !== "failed").length;

  return (
    <div className="rounded-xl border border-white/5 bg-white/[0.02] p-5 backdrop-blur-sm">
      <div className="mb-4 flex items-center justify-between">
        <h2 className="flex items-center gap-2 text-sm font-semibold">
          <Video className="h-4 w-4 text-rose-400" />
          Video Production
        </h2>
        <div className="flex gap-3 text-[10px]">
          <span className="text-emerald-400">{completed} rendered</span>
          <span className="text-cyan-400">{rendering} in progress</span>
        </div>
      </div>

      {/* Production Pipeline */}
      <div className="mb-4 flex items-center justify-between rounded-lg bg-white/5 px-3 py-2 text-[10px]">
        {["Queued", "TTS Synthesis", "Avatar Render", "Complete"].map((step, i) => (
          <div key={step} className="flex items-center gap-1">
            <span className={`h-1.5 w-1.5 rounded-full ${i <= 2 ? "bg-cyan-400" : "bg-emerald-400"}`} />
            <span className="text-white/40">{step}</span>
            {i < 3 && <span className="mx-1 text-white/15">→</span>}
          </div>
        ))}
      </div>

      {/* Job List */}
      <div className="space-y-2">
        <AnimatePresence>
          {jobs.map((job) => {
            const cfg = STATUS_MAP[job.status];
            return (
              <motion.div
                key={job.id}
                layout
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                className="relative overflow-hidden rounded-lg border border-white/5 bg-white/[0.02] p-3"
              >
                <div className="flex items-start justify-between gap-2">
                  <div className="min-w-0 flex-1">
                    <div className="truncate text-xs font-medium">{job.headline}</div>
                    <div className="mt-0.5 flex items-center gap-2 text-[10px] text-muted">
                      <span className="rounded bg-white/10 px-1 py-0.5 text-[9px] font-bold">{job.language}</span>
                      <cfg.Icon className={`h-3 w-3 ${cfg.color} ${job.status === "rendering" || job.status === "tts" ? "animate-spin" : ""}`} />
                      <span className={cfg.color}>{cfg.label}</span>
                      <span className="ml-auto">{job.createdAt}</span>
                    </div>
                  </div>
                  {job.status === "complete" && (
                    <button className="shrink-0 rounded-lg bg-emerald-500/10 p-1.5 text-emerald-400 hover:bg-emerald-500/20">
                      <PlayCircle className="h-4 w-4" />
                    </button>
                  )}
                </div>

                {/* Progress bar */}
                {job.status !== "complete" && job.status !== "failed" && (
                  <div className="mt-2 h-1 w-full overflow-hidden rounded-full bg-white/5">
                    <motion.div
                      className="h-full rounded-full bg-gradient-to-r from-violet-500 via-cyan-500 to-emerald-500"
                      animate={{ width: `${job.progress}%` }}
                      transition={{ duration: 0.5 }}
                    />
                  </div>
                )}

                {job.status === "complete" && (
                  <div className="mt-1.5 flex gap-3 text-[9px] text-muted">
                    <span>Duration: {job.duration}</span>
                    <span>Format: MP4 1080p</span>
                    <span>Avatar: AI Anchor v2</span>
                  </div>
                )}
              </motion.div>
            );
          })}
        </AnimatePresence>
      </div>
    </div>
  );
}
