"use client";

import Link from "next/link";
import { Radio } from "lucide-react";

export function Header() {
  return (
    <header className="sticky top-0 z-40 border-b border-white/5 bg-[#080810]/80 backdrop-blur-xl">
      <div className="mx-auto flex h-14 max-w-7xl items-center justify-between px-4">
        <Link href="/" className="flex items-center gap-2">
          <Radio className="h-5 w-5 text-cyan-400" />
          <div>
            <div className="text-sm font-bold leading-none">A.N.N.</div>
            <div className="text-[10px] text-muted">AI News Network</div>
          </div>
        </Link>

        <nav className="flex items-center gap-4 text-sm">
          <Link href="/dashboard" className="text-muted hover:text-white transition-colors">
            Dashboard
          </Link>
          <Link href="/news" className="text-muted hover:text-white transition-colors">
            News
          </Link>
          <Link href="/portal" className="text-muted hover:text-white transition-colors">
            Portal
          </Link>
        </nav>

        <div className="flex items-center gap-3">
          <div className="flex items-center gap-1.5 text-xs">
            <span className="live-dot h-2 w-2 rounded-full bg-red-500" />
            <span className="font-semibold text-red-400">LIVE</span>
          </div>
        </div>
      </div>
    </header>
  );
}
