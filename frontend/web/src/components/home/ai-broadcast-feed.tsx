"use client";

import { motion } from "framer-motion";
import { useNewsStore } from "@/lib/store";
import { timeAgo, CAT_COLORS } from "@/lib/utils";
import { Radio, Play, Clock, FileText, Globe } from "lucide-react";

export function AiBroadcastFeed() {
  const scripts = useNewsStore((s) => s.scripts);
  const broadcasts = scripts.slice(0, 6);

  return (
    <section className="mx-auto w-full max-w-7xl px-4 py-6">
      <div className="mb-4 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Radio className="h-4 w-4 text-violet-400" />
          <h2 className="text-sm font-semibold">AI Generated Broadcasts</h2>
          <span className="rounded bg-violet-500/10 px-1.5 py-0.5 text-[9px] font-bold text-violet-400">
            AUTONOMOUS
          </span>
        </div>
        <a href="/news" className="text-[10px] font-medium text-indigo-400 hover:text-indigo-300">
          View All Broadcasts →
        </a>
      </div>

      {broadcasts.length === 0 ? (
        <div className="rounded-2xl border border-white/5 bg-white/[0.02] p-12 text-center">
          <Radio className="mx-auto h-10 w-10 text-violet-500/30" />
          <h3 className="mt-3 text-sm font-semibold">AI Newsroom Standing By</h3>
          <p className="mt-1 text-xs text-muted">
            Go to the <a href="/dashboard" className="text-indigo-400 hover:underline">Control Center</a> to run the pipeline.
          </p>
        </div>
      ) : (
        <div className="grid gap-4 lg:grid-cols-3">
          {broadcasts.map((s, i) => (
            <motion.div
              key={s.id}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: i * 0.08 }}
              className="group overflow-hidden rounded-2xl border border-white/5 bg-white/[0.02] transition-colors hover:border-white/10"
            >
              {/* Video Thumbnail */}
              <div className="relative aspect-video bg-gradient-to-br from-[#0c0c1a] to-[#151530]">
                <div className="absolute inset-0 flex items-center justify-center">
                  <div className="text-4xl opacity-15">🤖</div>
                </div>
                <div className="absolute left-2 top-2 rounded bg-red-600/80 px-1.5 py-0.5 text-[8px] font-black text-white">
                  AI BROADCAST
                </div>
                <div className="absolute bottom-2 right-2 rounded bg-black/60 px-1.5 py-0.5 text-[9px] font-medium text-white/60">
                  ~{s.estimated_duration_seconds}s
                </div>
                <div className="absolute inset-0 flex items-center justify-center opacity-0 transition-opacity group-hover:opacity-100">
                  <div className="flex h-12 w-12 items-center justify-center rounded-full bg-white/20 backdrop-blur-sm">
                    <Play className="h-5 w-5 text-white" />
                  </div>
                </div>
              </div>

              {/* Content */}
              <div className="p-4">
                <div className="flex items-center gap-2">
                  <span
                    className="rounded px-1.5 py-0.5 text-[9px] font-bold uppercase"
                    style={{
                      color: CAT_COLORS[s.category] || CAT_COLORS.general,
                      background: `${CAT_COLORS[s.category] || CAT_COLORS.general}15`,
                    }}
                  >
                    {s.category}
                  </span>
                  <span className="text-[9px] text-muted">{timeAgo(s.created_at)}</span>
                </div>
                <h3 className="mt-2 text-sm font-semibold leading-tight group-hover:text-white">
                  {s.headline}
                </h3>
                <p className="mt-1.5 line-clamp-2 text-[11px] leading-relaxed text-white/30">
                  {s.english_script.replace(/\[PAUSE\]/g, "").substring(0, 150)}
                </p>

                {/* Meta */}
                <div className="mt-3 flex items-center gap-3 border-t border-white/5 pt-2.5 text-[9px] text-muted">
                  <span className="flex items-center gap-1"><FileText className="h-3 w-3" />{s.word_count_en} words</span>
                  <span className="flex items-center gap-1"><Clock className="h-3 w-3" />~{s.estimated_duration_seconds}s</span>
                  <span className="flex items-center gap-1"><Globe className="h-3 w-3" />5 languages</span>
                </div>
              </div>
            </motion.div>
          ))}
        </div>
      )}
    </section>
  );
}
