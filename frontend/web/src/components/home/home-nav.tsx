"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { Radio } from "lucide-react";
import { LocaleToggle, ThemeToggle } from "@/components/ui";

export function HomeNav() {
  const [clock, setClock] = useState("");

  useEffect(() => {
    const update = () =>
      setClock(
        new Date().toLocaleTimeString("en-US", {
          hour: "2-digit", minute: "2-digit", second: "2-digit", hour12: false,
        })
      );
    update();
    const id = setInterval(update, 1000);
    return () => clearInterval(id);
  }, []);

  return (
    <nav className="sticky top-0 z-50 border-b border-white/5 bg-[#080810]/95 backdrop-blur-xl">
      <div className="mx-auto flex h-14 max-w-7xl items-center justify-between px-4">
        <Link href="/" className="flex items-center gap-2.5">
          <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-gradient-to-br from-red-600 to-red-700">
            <Radio className="h-4 w-4 text-white" />
          </div>
          <div>
            <div className="text-sm font-black tracking-tight">A.N.N.</div>
            <div className="text-[9px] font-medium uppercase tracking-widest text-muted">AI News Network</div>
          </div>
        </Link>

        <div className="hidden items-center gap-6 text-xs font-medium md:flex">
          {["World", "Business", "Politics", "Technology", "Finance", "Sports"].map((cat) => (
            <Link
              key={cat}
              href={`/news?category=${cat.toLowerCase()}`}
              className="text-muted transition-colors hover:text-white"
            >
              {cat}
            </Link>
          ))}
        </div>

        <div className="flex items-center gap-3">
          <LocaleToggle />
          <ThemeToggle />
          <div className="flex items-center gap-1.5">
            <span className="live-dot h-2 w-2 rounded-full bg-red-500" />
            <span className="text-[10px] font-black text-red-400">LIVE</span>
          </div>
          <span className="hidden font-mono text-[10px] text-muted sm:block">{clock}</span>
          <Link
            href="/dashboard"
            className="rounded-lg border border-white/10 bg-white/5 px-3 py-1.5 text-[10px] font-medium text-muted hover:bg-white/10"
          >
            Control Center
          </Link>
        </div>
      </div>
    </nav>
  );
}
