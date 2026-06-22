"use client";

import { motion } from "framer-motion";
import { useNewsStore } from "@/lib/store";
import { timeAgo, CAT_COLORS } from "@/lib/utils";

export function NewsFeed() {
  const { filteredScripts, setActiveScript } = useNewsStore();

  if (filteredScripts.length === 0) {
    return (
      <div className="mx-auto w-full max-w-6xl px-4 py-12 text-center">
        <div className="text-3xl">📡</div>
        <h3 className="mt-2 text-sm font-semibold">No Broadcasts Available</h3>
        <p className="mt-1 text-xs text-muted">
          Go to the <a href="/" className="text-cyan-400 hover:underline">Admin Dashboard</a> to run the pipeline.
        </p>
      </div>
    );
  }

  return (
    <div className="mx-auto grid w-full max-w-6xl gap-4 px-4 pb-8 sm:grid-cols-2 lg:grid-cols-3">
      {filteredScripts.map((s, i) => (
        <motion.article
          key={s.id}
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: i * 0.05 }}
          onClick={() => setActiveScript(s)}
          className="group cursor-pointer overflow-hidden rounded-xl border border-white/5 bg-white/[0.02] transition-colors hover:border-white/10"
        >
          <div
            className="h-1"
            style={{ background: CAT_COLORS[s.category] || CAT_COLORS.general }}
          />
          <div className="p-4">
            <div
              className="text-[10px] font-semibold uppercase"
              style={{ color: CAT_COLORS[s.category] || CAT_COLORS.general }}
            >
              {s.category}
            </div>
            <h3 className="mt-1 text-sm font-semibold leading-tight group-hover:text-white">
              {s.headline}
            </h3>
            <p className="mt-2 line-clamp-3 text-xs leading-relaxed text-muted">
              {s.english_script.replace(/\[PAUSE\]/g, "").substring(0, 200)}
            </p>
          </div>
          <div className="border-t border-white/5 px-4 py-2">
            <div className="flex items-center gap-3 text-[10px] text-muted">
              <span>📝 {s.word_count_en} words</span>
              <span>⏱ ~{s.estimated_duration_seconds}s</span>
              <span className="ml-auto">{timeAgo(s.created_at)}</span>
            </div>
          </div>
        </motion.article>
      ))}
    </div>
  );
}
