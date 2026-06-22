"use client";

import { useDashboardStore } from "@/lib/store";
import { useForm } from "react-hook-form";
import { api } from "@/lib/api";
import { useToastStore } from "@/components/ui/toast";
import { useQueryClient } from "@tanstack/react-query";

const levelColors: Record<string, string> = {
  info: "text-blue-400 bg-blue-500/10",
  ok: "text-emerald-400 bg-emerald-500/10",
  error: "text-red-400 bg-red-500/10",
  warn: "text-amber-400 bg-amber-500/10",
};

export function ActivityLog() {
  const { logs, clearLogs, addLog } = useDashboardStore();
  const toast = useToastStore((s) => s.add);
  const queryClient = useQueryClient();

  const { register, handleSubmit, reset } = useForm<{
    source_url: string;
    raw_text: string;
  }>();

  const onSubmit = handleSubmit(async (data) => {
    if (!data.raw_text || data.raw_text.length < 50) {
      toast("Article text must be at least 50 characters", "warning");
      return;
    }
    addLog("info", "Processing manual article...");
    try {
      await api.processArticle({
        source_url: data.source_url || "manual-input",
        raw_text: data.raw_text,
        source_name: "Manual Input",
        category: "general",
      });
      toast("Article processed!", "success");
      queryClient.invalidateQueries({ queryKey: ["scripts"] });
      reset();
    } catch (e: any) {
      toast(`Failed: ${e.message}`, "error");
    }
  });

  return (
    <section className="space-y-4">
      {/* Manual Article Input */}
      <div className="rounded-xl border border-white/5 bg-white/[0.02] p-4">
        <h2 className="mb-3 flex items-center gap-2 text-sm font-semibold">✏️ Manual Article Input</h2>
        <form onSubmit={onSubmit} className="space-y-3">
          <input
            {...register("source_url")}
            placeholder="Source URL (optional)"
            className="w-full rounded-lg border border-white/10 bg-white/5 px-3 py-2 text-sm text-white placeholder:text-white/30 outline-none focus:border-indigo-500/50"
          />
          <textarea
            {...register("raw_text")}
            rows={4}
            placeholder="Paste article text here (min 50 chars)..."
            className="w-full resize-y rounded-lg border border-white/10 bg-white/5 px-3 py-2 text-sm text-white placeholder:text-white/30 outline-none focus:border-indigo-500/50"
          />
          <button
            type="submit"
            className="w-full rounded-lg bg-indigo-600 py-2 text-sm font-medium text-white hover:bg-indigo-500 transition-colors"
          >
            ⚡ Process Article
          </button>
        </form>
      </div>

      {/* Activity Log */}
      <div className="rounded-xl border border-white/5 bg-white/[0.02] p-4">
        <div className="mb-3 flex items-center justify-between">
          <h2 className="flex items-center gap-2 text-sm font-semibold">📊 Activity Log</h2>
          <button
            onClick={clearLogs}
            className="rounded-lg border border-white/10 bg-white/5 px-2 py-1 text-xs text-muted hover:bg-white/10"
          >
            Clear
          </button>
        </div>
        <div className="max-h-[250px] space-y-1 overflow-y-auto">
          {logs.length === 0 ? (
            <div className="py-4 text-center text-xs text-muted">No activity yet</div>
          ) : (
            logs.map((log, i) => (
              <div key={i} className="flex items-start gap-2 text-xs">
                <span className="shrink-0 font-mono text-muted">{log.time}</span>
                <span className={`shrink-0 rounded px-1.5 py-0.5 text-[10px] font-medium uppercase ${levelColors[log.level] || ""}`}>
                  {log.level}
                </span>
                <span className="text-muted">{log.message}</span>
              </div>
            ))
          )}
        </div>
      </div>
    </section>
  );
}
