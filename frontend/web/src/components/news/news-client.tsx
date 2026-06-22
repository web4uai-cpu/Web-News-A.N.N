"use client";

import { useEffect } from "react";
import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { useNewsStore } from "@/lib/store";
import { NewsNav } from "./news-nav";
import { BreakingTicker } from "./breaking-ticker";
import { HeroSection } from "./hero-section";
import { NewsFeed } from "./news-feed";
import { ScriptReader } from "./script-reader";
import { ToastContainer } from "@/components/ui/toast";

export function NewsClient() {
  const { setScripts } = useNewsStore();

  const { data: scripts } = useQuery({
    queryKey: ["news-scripts"],
    queryFn: () => api.scripts(50),
    refetchInterval: 30000,
  });

  useEffect(() => {
    if (scripts) setScripts(scripts);
  }, [scripts]);

  return (
    <div className="flex min-h-screen flex-col">
      <NewsNav />
      <BreakingTicker />

      {/* Enterprise Banner */}
      <div className="mx-auto w-full max-w-6xl px-4 pt-4">
        <div className="flex items-center justify-between rounded-xl border border-violet-500/30 bg-gradient-to-r from-indigo-500/10 to-violet-500/10 p-4">
          <div>
            <h3 className="text-sm font-semibold">📡 Developer API & Enterprise Webhooks</h3>
            <p className="text-xs text-muted">Stream real-time news data into your app or trading algorithm.</p>
          </div>
          <button className="rounded-lg bg-indigo-600 px-4 py-2 text-sm font-medium text-white hover:bg-indigo-500">
            Purchase API Key
          </button>
        </div>
      </div>

      <HeroSection />

      <div className="mx-auto w-full max-w-6xl px-4 py-2">
        <div className="flex items-center gap-3 text-xs text-muted">
          <span className="font-semibold">📰 Latest News Feed</span>
          <span className="h-px flex-1 bg-white/10" />
          <span>{useNewsStore.getState().filteredScripts.length} stories</span>
        </div>
      </div>

      <NewsFeed />

      {/* Footer */}
      <footer className="mt-auto border-t border-white/5 py-6 text-center text-xs text-muted">
        <div className="font-semibold">📺 A.N.N. — AI News Network</div>
        <div className="mt-2 flex justify-center gap-4">
          <a href="/" className="hover:text-white">Dashboard</a>
          <a href="/docs" className="hover:text-white">API Docs</a>
        </div>
        <div className="mt-2 flex items-center justify-center gap-1.5">
          <span className="h-1.5 w-1.5 rounded-full bg-emerald-500 live-dot" />
          All systems operational
        </div>
      </footer>

      <ScriptReader />
      <ToastContainer />
    </div>
  );
}
