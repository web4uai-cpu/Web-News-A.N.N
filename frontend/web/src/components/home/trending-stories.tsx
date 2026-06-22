"use client";

import { useMemo, useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { useNewsStore } from "@/lib/store";
import { timeAgo, CAT_COLORS } from "@/lib/utils";
import { TrendingUp, Globe, Briefcase, Landmark, Cpu, Trophy } from "lucide-react";

const SECTIONS = [
  { key: "all", label: "Trending", Icon: TrendingUp },
  { key: "geopolitics", label: "World", Icon: Globe },
  { key: "business", label: "Business", Icon: Briefcase },
  { key: "politics", label: "Politics", Icon: Landmark },
  { key: "technology", label: "Technology", Icon: Cpu },
  { key: "sports", label: "Sports", Icon: Trophy },
] as const;

export function TrendingStories() {
  const scripts = useNewsStore((s) => s.scripts);
  const [active, setActive] = useState("all");

  const filtered = useMemo(() => {
    const list = active === "all" ? scripts : scripts.filter((s) => s.category === active);
    return list.slice(0, 8);
  }, [scripts, active]);

  return (
    <section className="mx-auto w-full max-w-7xl px-4 py-6">
      {/* Section Header + Category Tabs */}
      <div className="mb-4 flex flex-wrap items-center gap-2">
        {SECTIONS.map((sec) => (
          <button
            key={sec.key}
            onClick={() => setActive(sec.key)}
            className={`flex items-center gap-1.5 rounded-full px-3 py-1.5 text-[11px] font-medium transition-colors ${
              active === sec.key
                ? "bg-white/10 text-white"
                : "text-white/30 hover:text-white/60"
            }`}
          >
            <sec.Icon className="h-3 w-3" />
            {sec.label}
          </button>
        ))}
      </div>

      {/* Stories Grid */}
      <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
        <AnimatePresence mode="popLayout">
          {filtered.length === 0 ? (
            <div className="col-span-full rounded-xl border border-white/5 bg-white/[0.02] p-8 text-center text-sm text-muted">
              No stories yet. Run the pipeline from the Control Center.
            </div>
          ) : (
            filtered.map((s, i) => (
              <motion.article
                key={s.id}
                layout
                initial={{ opacity: 0, y: 15 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, scale: 0.95 }}
                transition={{ delay: i * 0.04 }}
                className="group cursor-pointer rounded-xl border border-white/5 bg-white/[0.02] transition-colors hover:border-white/10"
              >
                <div className="h-1 rounded-t-xl" style={{ background: CAT_COLORS[s.category] || CAT_COLORS.general }} />
                <div className="p-3.5">
                  <div className="flex items-center justify-between">
                    <span
                      className="text-[9px] font-bold uppercase tracking-wider"
                      style={{ color: CAT_COLORS[s.category] || CAT_COLORS.general }}
                    >
                      {s.category}
                    </span>
                    <span className="text-[9px] text-muted">{timeAgo(s.created_at)}</span>
                  </div>
                  <h3 className="mt-1.5 text-xs font-semibold leading-tight group-hover:text-white">
                    {s.headline}
                  </h3>
                  <p className="mt-1.5 line-clamp-2 text-[11px] leading-relaxed text-white/30">
                    {s.english_script.replace(/\[PAUSE\]/g, "").substring(0, 120)}
                  </p>
                  <div className="mt-2 flex gap-2 text-[9px] text-muted">
                    <span>{s.word_count_en} words</span>
                    <span>~{s.estimated_duration_seconds}s</span>
                  </div>
                </div>
              </motion.article>
            ))
          )}
        </AnimatePresence>
      </div>
    </section>
  );
}
