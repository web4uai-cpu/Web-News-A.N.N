"use client";

import { useNewsStore } from "@/lib/store";

export function BreakingStrip() {
  const scripts = useNewsStore((s) => s.scripts);
  const headlines =
    scripts.length > 0
      ? scripts.slice(0, 12).map((s) => s.headline)
      : [
          "A.N.N. — The world's first autonomous AI news network is now live",
          "10 AI agents collaborating in real-time to produce broadcast-ready news",
          "Multi-language broadcasts available in English, Hindi, Spanish, French, and Arabic",
        ];

  return (
    <div className="flex h-8 items-center overflow-hidden border-b border-white/5 bg-[#0a0a14]">
      <div className="flex h-full shrink-0 items-center gap-1.5 bg-red-600 px-3">
        <span className="live-dot h-1.5 w-1.5 rounded-full bg-white" />
        <span className="text-[10px] font-black text-white">BREAKING</span>
      </div>
      <div className="relative flex-1 overflow-hidden">
        <div className="ticker-animate flex whitespace-nowrap">
          {[...headlines, ...headlines].map((h, i) => (
            <span key={i} className="flex items-center">
              <span className="px-4 text-[11px] text-white/60">{h}</span>
              <span className="text-[8px] text-red-500/40">///</span>
            </span>
          ))}
        </div>
      </div>
    </div>
  );
}
