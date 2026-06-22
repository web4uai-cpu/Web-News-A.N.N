"use client";

import { useNewsStore } from "@/lib/store";

export function BreakingTicker() {
  const scripts = useNewsStore((s) => s.scripts);
  const headlines =
    scripts.length > 0
      ? scripts.slice(0, 15).map((s) => s.headline)
      : [
          "A.N.N. — AI News Network is now live",
          "Autonomous AI-powered news broadcasting system operational",
          "Multi-lingual broadcasts available in English and Hindi",
        ];

  return (
    <div className="flex h-8 items-center overflow-hidden border-b border-white/5 bg-[#0c0c18]">
      <div className="flex h-full shrink-0 items-center bg-red-600 px-3 text-[10px] font-black text-white">
        ⚡ BREAKING
      </div>
      <div className="relative flex-1 overflow-hidden">
        <div className="ticker-animate flex whitespace-nowrap">
          {[...headlines, ...headlines].map((h, i) => (
            <span key={i} className="flex items-center">
              <span className="px-4 text-xs text-muted">{h}</span>
              <span className="text-[8px] text-white/20">◆</span>
            </span>
          ))}
        </div>
      </div>
    </div>
  );
}
