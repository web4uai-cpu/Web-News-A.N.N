"use client";

import { useEffect, useState } from "react";
import { motion } from "framer-motion";
import {
  LayoutDashboard, Terminal, Settings, Video, Power, Radio,
} from "lucide-react";
import { useAuthStore } from "@/lib/auth-store";
import { OverviewTab } from "./tabs/overview-tab";
import { ApiTab } from "./tabs/api-tab";
import { SocialTab } from "./tabs/social-tab";
import { StudioTab } from "./tabs/studio-tab";
import { LoginScreen } from "./login-screen";
import { ToastContainer } from "@/components/ui/toast";

const TABS = [
  { id: "overview", label: "Command Center", icon: LayoutDashboard, category: "Global Overview" },
  { id: "api", label: "Developer API", icon: Terminal, category: "B2B Enterprise" },
  { id: "social", label: "Matrix Config", icon: Settings, category: "Social Media" },
  { id: "studio", label: "Synthesis Engine", icon: Video, category: "Social Media" },
] as const;

export function PortalClient() {
  const [activeTab, setActiveTab] = useState("overview");
  const { user, loading, initialize, signOut } = useAuthStore();

  useEffect(() => {
    initialize();
  }, []);

  if (loading) {
    return (
      <div className="flex min-h-screen items-center justify-center">
        <div className="h-8 w-8 animate-spin rounded-full border-2 border-violet-500 border-t-transparent" />
      </div>
    );
  }

  if (!user) {
    return (
      <>
        <LoginScreen />
        <ToastContainer />
      </>
    );
  }

  const email = user.email || "";

  return (
    <>
      <div className="flex h-screen overflow-hidden">
        {/* Sidebar */}
        <aside className="flex w-72 flex-col border-r border-white/5 bg-[#0a0a12]/80 p-6 backdrop-blur-xl">
          <div className="mb-10 flex items-center gap-3">
            <Radio className="h-6 w-6 text-cyan-400 drop-shadow-[0_0_10px_rgba(6,182,212,0.5)]" />
            <span className="text-xl font-black tracking-tight">A.N.N. Node</span>
          </div>

          {(() => {
            let lastCat = "";
            return TABS.map((tab) => {
              const showCat = tab.category !== lastCat;
              lastCat = tab.category;
              return (
                <div key={tab.id}>
                  {showCat && (
                    <div className="mb-2 mt-4 text-[10px] font-extrabold uppercase tracking-widest text-white/20">
                      {tab.category}
                    </div>
                  )}
                  <button
                    onClick={() => setActiveTab(tab.id)}
                    className={`relative mb-1 flex w-full items-center gap-3 rounded-2xl px-4 py-3 text-sm font-medium transition-colors ${
                      activeTab === tab.id
                        ? "bg-violet-500/10 text-white"
                        : "text-muted hover:bg-violet-500/5 hover:text-white"
                    }`}
                  >
                    {activeTab === tab.id && (
                      <motion.div
                        layoutId="sidebar-indicator"
                        className="absolute -left-6 top-1/2 h-5 w-1 -translate-y-1/2 rounded-r bg-violet-500 shadow-[0_0_10px_rgba(139,92,246,1)]"
                      />
                    )}
                    <tab.icon className="h-4 w-4" />
                    {tab.label}
                  </button>
                </div>
              );
            });
          })()}

          <div className="mt-auto">
            <div className="mb-2 truncate text-xs text-muted">{email}</div>
            <button
              onClick={signOut}
              className="flex w-full items-center gap-3 rounded-2xl px-4 py-3 text-sm font-medium text-red-400 transition-colors hover:bg-red-500/10"
            >
              <Power className="h-4 w-4" /> Terminate Session
            </button>
          </div>
        </aside>

        {/* Main */}
        <main className="flex-1 overflow-y-auto p-8">
          <header className="mb-8 flex items-end justify-between">
            <div>
              <h1 className="text-3xl font-black tracking-tight">
                {activeTab === "overview" && `Welcome, Director ${email.split("@")[0]}`}
                {activeTab === "api" && "Developer API"}
                {activeTab === "social" && "Social Auto-Pilot"}
                {activeTab === "studio" && "Synthesis Engine"}
              </h1>
              <p className="mt-1 text-muted">Enterprise data pipelines synchronized and operational.</p>
            </div>
            <span className="rounded-full border border-violet-500 bg-violet-500/10 px-4 py-2 text-xs font-extrabold uppercase tracking-widest text-violet-300 shadow-[0_0_20px_rgba(139,92,246,0.2)] animate-pulse">
              ENTERPRISE TIER
            </span>
          </header>

          {activeTab === "overview" && <OverviewTab />}
          {activeTab === "api" && <ApiTab />}
          {activeTab === "social" && <SocialTab />}
          {activeTab === "studio" && <StudioTab />}
        </main>
      </div>
      <ToastContainer />
    </>
  );
}
