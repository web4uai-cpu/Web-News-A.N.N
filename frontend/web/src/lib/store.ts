import { create } from "zustand";
import type { Script, PipelineJob } from "./api";

interface LogEntry {
  time: string;
  level: "info" | "ok" | "error" | "warn";
  message: string;
}

interface DashboardState {
  scripts: Script[];
  setScripts: (scripts: Script[]) => void;
  addScript: (script: Script) => void;

  activeJob: string | null;
  setActiveJob: (jobId: string | null) => void;

  logs: LogEntry[];
  addLog: (level: LogEntry["level"], message: string) => void;
  clearLogs: () => void;

  stats: {
    uptime: string;
    activeJobs: number;
    scriptsGenerated: number;
    articlesProcessed: number;
  };
  updateStats: (partial: Partial<DashboardState["stats"]>) => void;

  isApiOnline: boolean;
  setApiOnline: (online: boolean) => void;
}

export const useDashboardStore = create<DashboardState>((set) => ({
  scripts: [],
  setScripts: (scripts) =>
    set({ scripts }),
  addScript: (script) =>
    set((s) => ({ scripts: [script, ...s.scripts] })),

  activeJob: null,
  setActiveJob: (jobId) => set({ activeJob: jobId }),

  logs: [],
  addLog: (level, message) =>
    set((s) => ({
      logs: [
        {
          time: new Date().toLocaleTimeString("en-US", { hour12: false }),
          level,
          message,
        },
        ...s.logs,
      ].slice(0, 100),
    })),
  clearLogs: () => set({ logs: [] }),

  stats: {
    uptime: "0s",
    activeJobs: 0,
    scriptsGenerated: 0,
    articlesProcessed: 0,
  },
  updateStats: (partial) =>
    set((s) => ({ stats: { ...s.stats, ...partial } })),

  isApiOnline: false,
  setApiOnline: (online) => set({ isApiOnline: online }),
}));

interface NewsState {
  scripts: Script[];
  filteredScripts: Script[];
  activeCategory: string;
  activeScript: Script | null;
  readerLang: "en" | "hi" | "es" | "fr" | "ar";

  setScripts: (scripts: Script[]) => void;
  setActiveCategory: (cat: string) => void;
  setActiveScript: (script: Script | null) => void;
  setReaderLang: (lang: "en" | "hi" | "es" | "fr" | "ar") => void;
}

export const useNewsStore = create<NewsState>((set, get) => ({
  scripts: [],
  filteredScripts: [],
  activeCategory: "all",
  activeScript: null,
  readerLang: "en",

  setScripts: (scripts) => {
    const cat = get().activeCategory;
    set({
      scripts,
      filteredScripts:
        cat === "all" ? scripts : scripts.filter((s) => s.category === cat),
    });
  },
  setActiveCategory: (cat) =>
    set((s) => ({
      activeCategory: cat,
      filteredScripts:
        cat === "all" ? s.scripts : s.scripts.filter((sc) => sc.category === cat),
    })),
  setActiveScript: (script) => set({ activeScript: script, readerLang: "en" }),
  setReaderLang: (lang) => set({ readerLang: lang }),
}));
