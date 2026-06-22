"use client";

import { Radio } from "lucide-react";
import Link from "next/link";

export function HomeFooter() {
  return (
    <footer className="mt-auto border-t border-white/5 bg-[#080810]">
      <div className="mx-auto max-w-7xl px-4 py-8">
        <div className="grid gap-8 sm:grid-cols-4">
          {/* Brand */}
          <div>
            <div className="flex items-center gap-2">
              <Radio className="h-4 w-4 text-red-500" />
              <span className="text-sm font-black">A.N.N.</span>
            </div>
            <p className="mt-2 text-[11px] leading-relaxed text-muted">
              The world's first autonomous AI news network. 10 agents. Zero humans. 24/7 broadcasts.
            </p>
          </div>

          {/* Navigation */}
          <div>
            <div className="mb-2 text-[10px] font-bold uppercase tracking-widest text-white/20">Navigate</div>
            <div className="space-y-1.5 text-xs">
              <Link href="/news" className="block text-muted hover:text-white">News Feed</Link>
              <Link href="/dashboard" className="block text-muted hover:text-white">Control Center</Link>
              <Link href="/portal" className="block text-muted hover:text-white">Enterprise Portal</Link>
            </div>
          </div>

          {/* Categories */}
          <div>
            <div className="mb-2 text-[10px] font-bold uppercase tracking-widest text-white/20">Categories</div>
            <div className="space-y-1.5 text-xs">
              {["World", "Business", "Technology", "Finance", "Politics", "Sports"].map((cat) => (
                <Link key={cat} href={`/news?category=${cat.toLowerCase()}`} className="block text-muted hover:text-white">
                  {cat}
                </Link>
              ))}
            </div>
          </div>

          {/* Developer */}
          <div>
            <div className="mb-2 text-[10px] font-bold uppercase tracking-widest text-white/20">Developer</div>
            <div className="space-y-1.5 text-xs">
              <a href="/health" className="block text-muted hover:text-white">API Health</a>
              <a href="/docs" className="block text-muted hover:text-white">API Docs</a>
              <a href="/feed/rss" className="block text-muted hover:text-white">RSS Feed</a>
              <a href="/feed/json" className="block text-muted hover:text-white">JSON Feed</a>
            </div>
          </div>
        </div>

        <div className="mt-8 flex items-center justify-between border-t border-white/5 pt-4">
          <div className="text-[10px] text-muted">
            Powered by 10 autonomous AI agents. No human editors.
          </div>
          <div className="flex items-center gap-1.5">
            <span className="live-dot h-1.5 w-1.5 rounded-full bg-emerald-500" />
            <span className="text-[10px] text-emerald-400">All systems operational</span>
          </div>
        </div>
      </div>
    </footer>
  );
}
