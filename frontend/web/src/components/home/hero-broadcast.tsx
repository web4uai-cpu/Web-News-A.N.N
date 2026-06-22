"use client";

import { motion } from "framer-motion";
import { useNewsStore } from "@/lib/store";
import { timeAgo } from "@/lib/utils";
import { Play, Volume2, Maximize2 } from "lucide-react";

export function HeroBroadcast() {
  const scripts = useNewsStore((s) => s.scripts);
  const featured = scripts[0];
  const sidebar = scripts.slice(1, 5);

  return (
    <section className="mx-auto w-full max-w-7xl px-4 pt-4">
      <div className="grid gap-4 lg:grid-cols-[3fr_1fr]">
        {/* Main Broadcast Frame */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="relative overflow-hidden rounded-2xl border border-white/5 bg-gradient-to-br from-[#0c0c1a] via-[#111128] to-[#0c0c1a]"
        >
          {/* Video Frame */}
          <div className="relative aspect-video w-full bg-[#080818]">
            {/* Studio Background */}
            <div className="absolute inset-0 flex items-center justify-center">
              <div className="relative">
                <div className="text-7xl opacity-20">🤖</div>
                <motion.div
                  className="absolute -inset-8 rounded-full border border-cyan-500/10"
                  animate={{ scale: [1, 1.2, 1], opacity: [0.3, 0.1, 0.3] }}
                  transition={{ duration: 3, repeat: Infinity }}
                />
              </div>
            </div>

            {/* Network Bug */}
            <div className="absolute left-4 top-4 flex items-center gap-2">
              <div className="rounded bg-red-600/90 px-2 py-0.5 text-[10px] font-black text-white">A.N.N. LIVE</div>
              <div className="flex items-center gap-1 rounded bg-black/50 px-2 py-0.5">
                <span className="live-dot h-1.5 w-1.5 rounded-full bg-red-500" />
                <span className="text-[9px] font-bold text-red-400">REC</span>
              </div>
            </div>

            {/* Controls */}
            <div className="absolute bottom-4 left-4 right-4 flex items-center justify-between">
              <div className="flex items-center gap-2">
                <button className="flex h-10 w-10 items-center justify-center rounded-full bg-white/10 text-white backdrop-blur-sm hover:bg-white/20">
                  <Play className="h-5 w-5" />
                </button>
                <button className="rounded-lg bg-white/10 p-2 text-white/60 backdrop-blur-sm hover:text-white">
                  <Volume2 className="h-4 w-4" />
                </button>
              </div>
              <div className="flex items-center gap-2">
                <span className="rounded bg-black/50 px-2 py-0.5 text-[10px] font-medium text-white/40">HD 1080p</span>
                <button className="rounded-lg bg-white/10 p-2 text-white/60 backdrop-blur-sm hover:text-white">
                  <Maximize2 className="h-4 w-4" />
                </button>
              </div>
            </div>

            {/* Lower Third */}
            <div className="absolute bottom-0 left-0 right-0 bg-gradient-to-t from-black/90 via-black/60 to-transparent px-6 pb-16 pt-20">
              <div className="flex items-center gap-2">
                <span className="rounded bg-red-600 px-1.5 py-0.5 text-[9px] font-black text-white">BREAKING</span>
                {featured && (
                  <span className="rounded bg-white/10 px-1.5 py-0.5 text-[9px] font-medium uppercase text-white/60">
                    {featured.category}
                  </span>
                )}
              </div>
              <h1 className="mt-2 text-xl font-bold leading-tight text-white lg:text-2xl">
                {featured?.headline || "A.N.N. — AI News Network"}
              </h1>
              <p className="mt-1.5 line-clamp-2 max-w-2xl text-sm text-white/50">
                {featured
                  ? featured.english_script.replace(/\[PAUSE\]/g, "").substring(0, 200) + "..."
                  : "The world's first autonomous AI news network. 10 AI agents producing broadcast-ready content 24/7."}
              </p>
            </div>
          </div>

          {/* Anchor Info Bar */}
          <div className="flex items-center justify-between border-t border-white/5 px-4 py-2.5">
            <div className="flex items-center gap-3">
              <div className="flex h-7 w-7 items-center justify-center rounded-full bg-gradient-to-br from-cyan-500 to-violet-500 text-xs">
                AI
              </div>
              <div>
                <div className="text-xs font-semibold">AI Anchor</div>
                <div className="text-[10px] text-muted">A.N.N. Autonomous Newsdesk</div>
              </div>
            </div>
            <div className="flex items-center gap-1.5">
              <span className="live-dot h-2 w-2 rounded-full bg-emerald-500" />
              <span className="text-[10px] font-medium text-emerald-400">ON AIR</span>
            </div>
          </div>
        </motion.div>

        {/* Sidebar — Breaking News Stack */}
        <div className="space-y-2">
          <div className="text-[10px] font-bold uppercase tracking-widest text-red-400">Breaking News</div>
          {sidebar.length === 0 ? (
            <div className="rounded-xl border border-white/5 bg-white/[0.02] p-4 text-xs text-muted">
              Waiting for AI pipeline...
            </div>
          ) : (
            sidebar.map((s, i) => (
              <motion.div
                key={s.id}
                initial={{ opacity: 0, x: 20 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: i * 0.1 }}
                className="group cursor-pointer rounded-xl border border-white/5 bg-white/[0.02] p-3 transition-colors hover:border-white/10 hover:bg-white/[0.04]"
              >
                <div className="text-[10px] font-semibold uppercase text-indigo-400">{s.category}</div>
                <div className="mt-1 text-xs font-medium leading-tight group-hover:text-white">{s.headline}</div>
                <div className="mt-1.5 flex items-center gap-2 text-[9px] text-muted">
                  <span>{timeAgo(s.created_at)}</span>
                  <span>~{s.estimated_duration_seconds}s</span>
                </div>
              </motion.div>
            ))
          )}
        </div>
      </div>
    </section>
  );
}
