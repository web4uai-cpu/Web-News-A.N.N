"use client";

import { useEffect, useState } from "react";
import { motion } from "framer-motion";
import { Activity, Satellite } from "lucide-react";

const FEED_MESSAGES = [
  "Pipeline [G-42] digested 1,402 articles in Tokyo.",
  "Vector database sync complete. 0ms latency.",
  "Render Node 09 generated Avatar Asset for User #81.",
  "Websocket packet verified. Secure connection stable.",
  "Sub-agent scraped 5 financial RSS feeds.",
];

export function OverviewTab() {
  const [feed, setFeed] = useState<{ time: string; msg: string }[]>([]);
  const quotaUsed = 1250;
  const quotaMax = 100000;
  const fillPercent = (quotaUsed / quotaMax) * 100;

  useEffect(() => {
    const id = setInterval(() => {
      const msg = FEED_MESSAGES[Math.floor(Math.random() * FEED_MESSAGES.length)];
      setFeed((prev) => [{ time: new Date().toLocaleTimeString(), msg }, ...prev].slice(0, 5));
    }, 3500);
    return () => clearInterval(id);
  }, []);

  return (
    <div className="grid gap-6 lg:grid-cols-2">
      {/* Quota Card */}
      <GlassCard>
        <div className="mb-6 flex items-center gap-3 text-xs font-semibold uppercase tracking-wider text-muted">
          <Activity className="h-4 w-4" /> Neural Interface Quota
        </div>
        <div className="flex items-center gap-8">
          <div className="relative flex h-32 w-32 items-center justify-center">
            <svg className="absolute inset-0" viewBox="0 0 36 36">
              <path
                d="M18 2.0845a 15.9155 15.9155 0 0 1 0 31.831a 15.9155 15.9155 0 0 1 0 -31.831"
                fill="none"
                stroke="rgba(255,255,255,0.05)"
                strokeWidth="3"
              />
              <motion.path
                d="M18 2.0845a 15.9155 15.9155 0 0 1 0 31.831a 15.9155 15.9155 0 0 1 0 -31.831"
                fill="none"
                stroke="url(#gradient)"
                strokeWidth="3"
                strokeLinecap="round"
                initial={{ strokeDasharray: "0 100" }}
                animate={{ strokeDasharray: `${fillPercent} ${100 - fillPercent}` }}
                transition={{ duration: 1.5, ease: "easeOut" }}
              />
              <defs>
                <linearGradient id="gradient">
                  <stop offset="0%" stopColor="#06b6d4" />
                  <stop offset="100%" stopColor="#8b5cf6" />
                </linearGradient>
              </defs>
            </svg>
            <span className="text-2xl font-black">{fillPercent.toFixed(1)}%</span>
          </div>
          <div>
            <div className="text-3xl font-black">{quotaUsed.toLocaleString()}</div>
            <div className="text-sm text-muted">out of {quotaMax.toLocaleString()} cycles</div>
            <div className="mt-1 text-xs text-cyan-400">Recharges in 14.3 cycles</div>
          </div>
        </div>
      </GlassCard>

      {/* Live Feed */}
      <GlassCard>
        <div className="mb-6 flex items-center gap-3 text-xs font-semibold uppercase tracking-wider text-muted">
          <Satellite className="h-4 w-4" /> Live Data Firehose
        </div>
        <div className="space-y-3">
          {feed.map((item, i) => (
            <motion.div
              key={i}
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              className="flex items-start gap-3"
            >
              <span className="mt-1.5 h-2 w-2 shrink-0 rounded-full bg-cyan-400 shadow-[0_0_10px_rgba(6,182,212,0.5)]" />
              <div className="text-xs">
                <span className="font-medium text-muted">{item.time}</span> — {item.msg}
              </div>
            </motion.div>
          ))}
          {feed.length === 0 && <div className="text-xs text-muted">Initializing data streams...</div>}
        </div>
      </GlassCard>
    </div>
  );
}

function GlassCard({ children }: { children: React.ReactNode }) {
  return (
    <div className="rounded-[30px] border border-white/5 bg-glass p-8 shadow-[inset_0_0_20px_rgba(0,0,0,0.5)] backdrop-blur-xl transition-transform hover:-translate-y-1 hover:border-white/10">
      {children}
    </div>
  );
}
