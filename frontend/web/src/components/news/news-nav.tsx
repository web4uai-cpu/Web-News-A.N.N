"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { useNewsStore } from "@/lib/store";
import { CATEGORIES } from "@/lib/utils";

export function NewsNav() {
  const { activeCategory, setActiveCategory } = useNewsStore();
  const [clock, setClock] = useState("");

  useEffect(() => {
    const update = () =>
      setClock(
        new Date().toLocaleDateString("en-US", {
          weekday: "short", month: "short", day: "numeric",
          hour: "2-digit", minute: "2-digit", second: "2-digit", hour12: false,
        })
      );
    update();
    const id = setInterval(update, 1000);
    return () => clearInterval(id);
  }, []);

  return (
    <nav className="sticky top-0 z-40 border-b border-white/5 bg-[#080810]/90 backdrop-blur-xl">
      <div className="mx-auto flex h-12 max-w-6xl items-center gap-4 px-4">
        <Link href="/news" className="flex items-center gap-2">
          <div className="flex h-7 w-10 items-center justify-center rounded bg-red-600 text-[10px] font-black text-white">
            ANN
          </div>
          <div>
            <div className="text-xs font-bold leading-none">A.N.N.</div>
            <div className="text-[9px] text-muted">AI News Network</div>
          </div>
        </Link>

        <div className="flex items-center gap-1.5 text-xs">
          <span className="live-dot h-2 w-2 rounded-full bg-red-500" />
          <span className="font-bold text-red-400">LIVE</span>
        </div>

        <div className="hidden flex-1 items-center gap-1 overflow-x-auto md:flex">
          {CATEGORIES.map((cat) => (
            <button
              key={cat.key}
              onClick={() => setActiveCategory(cat.key)}
              className={`shrink-0 rounded-full px-2.5 py-1 text-[11px] font-medium transition-colors ${
                activeCategory === cat.key
                  ? "bg-red-600/20 text-red-400"
                  : "text-muted hover:text-white"
              }`}
            >
              {cat.label}
            </button>
          ))}
        </div>

        <div className="ml-auto text-[10px] font-mono text-muted">{clock}</div>
      </div>
    </nav>
  );
}
