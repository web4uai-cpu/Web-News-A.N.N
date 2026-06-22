"use client";

import { motion } from "framer-motion";
import { useNewsStore } from "@/lib/store";
import { timeAgo } from "@/lib/utils";

export function HeroSection() {
  const { scripts, setActiveScript } = useNewsStore();
  const featured = scripts[0];
  const sidebar = scripts.slice(1, 7);

  return (
    <section className="mx-auto grid w-full max-w-6xl gap-4 p-4 lg:grid-cols-[2fr_1fr]">
      {/* Main Featured Story */}
      <motion.article
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        onClick={() => featured && setActiveScript(featured)}
        className="relative flex min-h-[320px] cursor-pointer flex-col justify-end overflow-hidden rounded-xl border border-white/5 bg-gradient-to-br from-[#0f0f1e] to-[#1a1a2e] p-6"
      >
        {/* Studio Frame */}
        <div className="absolute inset-0 flex items-center justify-center opacity-20">
          <div className="text-center">
            <div className="text-4xl">🤖</div>
            <div className="mt-1 text-xs font-bold text-muted">AI Anchor</div>
          </div>
        </div>

        <div className="absolute left-4 top-4 flex items-center gap-3">
          <span className="rounded bg-white/10 px-2 py-0.5 text-[10px] font-bold">A.N.N. HD</span>
          <span className="flex items-center gap-1 rounded bg-red-600/80 px-2 py-0.5 text-[10px] font-bold">
            <span className="live-dot h-1.5 w-1.5 rounded-full bg-white" />
            REC
          </span>
        </div>

        <div className="relative z-10">
          <span className="inline-block rounded bg-red-600/80 px-2 py-0.5 text-[10px] font-bold">
            ⚡ FEATURED
          </span>
          <h1 className="mt-2 text-xl font-bold leading-tight lg:text-2xl">
            {featured?.headline || "A.N.N. — AI News Network"}
          </h1>
          <p className="mt-2 line-clamp-3 text-sm text-muted">
            {featured
              ? featured.english_script.replace(/\[PAUSE\]/g, "").substring(0, 250) + "..."
              : "Your autonomous AI-powered news broadcast system is online. Use the admin dashboard to ingest news."}
          </p>
          <div className="mt-3 flex items-center gap-2 text-[10px] text-muted">
            {featured && (
              <>
                <span className="rounded bg-white/10 px-1.5 py-0.5 font-medium uppercase">
                  {featured.category}
                </span>
                <span>{timeAgo(featured.created_at)}</span>
                <span>•</span>
                <span>~{featured.estimated_duration_seconds}s</span>
              </>
            )}
          </div>
        </div>
      </motion.article>

      {/* Sidebar Headlines */}
      <aside className="rounded-xl border border-white/5 bg-white/[0.02]">
        <div className="border-b border-white/5 p-3 text-xs font-semibold">📋 Latest Headlines</div>
        <div className="divide-y divide-white/5">
          {sidebar.length === 0 ? (
            <div className="p-3 text-xs text-muted">Waiting for news scripts...</div>
          ) : (
            sidebar.map((s) => (
              <div
                key={s.id}
                onClick={() => setActiveScript(s)}
                className="cursor-pointer p-3 transition-colors hover:bg-white/5"
              >
                <div className="text-[10px] font-semibold uppercase text-indigo-400">{s.category}</div>
                <div className="mt-0.5 text-xs font-medium leading-tight">{s.headline}</div>
                <div className="mt-1 text-[10px] text-muted">{timeAgo(s.created_at)}</div>
              </div>
            ))
          )}
        </div>
      </aside>
    </section>
  );
}
