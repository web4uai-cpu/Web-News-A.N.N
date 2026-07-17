"use client";

import { useState, useCallback } from "react";
import { motion } from "framer-motion";
import { api } from "@/lib/api";
import { useDashboardStore } from "@/lib/store";
import { useToastStore } from "@/components/ui/toast";
import { PIPELINE_STEPS } from "@/lib/utils";
import { Rocket } from "lucide-react";
import { Button } from "@/components/ui";

const SOURCES = [
  { value: "newsapi", label: "📰 NewsAPI" },
  { value: "financial", label: "📈 Alpha Vantage" },
  { value: "gdelt", label: "🌍 GDELT" },
];

const CATEGORY_OPTIONS = [
  "general", "business", "technology", "science",
  "health", "sports", "entertainment", "politics", "finance", "geopolitics",
];

export function PipelineControl() {
  const { addLog, setActiveJob, activeJob } = useDashboardStore();
  const toast = useToastStore((s) => s.add);
  const [running, setRunning] = useState(false);
  const [source, setSource] = useState("newsapi");
  const [category, setCategory] = useState("general");
  const [query, setQuery] = useState("");
  const [maxArticles, setMaxArticles] = useState(5);
  const [generateMedia, setGenerateMedia] = useState(false);
  const [currentStep, setCurrentStep] = useState(-1);

  const runPipeline = useCallback(async () => {
    setRunning(true);
    addLog("info", `Starting pipeline: source=${source}, category=${category}`);
    toast("Pipeline started...", "info");
    try {
      const result = await api.runPipeline({
        source,
        category,
        query: query || undefined,
        max_articles: maxArticles,
        generate_media: generateMedia,
      });
      setActiveJob(result.job_id);
      addLog("ok", `Pipeline job created: ${result.job_id}`);
      toast(`Job ${result.job_id.slice(0, 8)}... started`, "success");
      setCurrentStep(1);
    } catch (e: any) {
      toast(`Pipeline failed: ${e.message}`, "error");
      addLog("error", `Pipeline failed: ${e.message}`);
    } finally {
      setRunning(false);
    }
  }, [source, category, query, maxArticles, generateMedia]);

  const selectClass =
    "w-full rounded-lg border border-edge-strong bg-surface px-3 py-2 text-sm text-foreground outline-none focus:border-indigo-500/50 focus:ring-1 focus:ring-indigo-500/30";

  return (
    <motion.section
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: 0.25 }}
      className="rounded-xl border border-edge bg-surface p-5 backdrop-blur-sm"
    >
      <h2 className="mb-4 flex items-center gap-2 text-sm font-semibold">
        🎛️ Pipeline Control
      </h2>

      <div className="flex flex-wrap items-end gap-3">
        <div className="min-w-[140px]">
          <label htmlFor="pc-source" className="mb-1 block text-xs text-muted">Source</label>
          <select id="pc-source" className={selectClass} value={source} onChange={(e) => setSource(e.target.value)}>
            {SOURCES.map((s) => (
              <option key={s.value} value={s.value}>{s.label}</option>
            ))}
          </select>
        </div>

        <div className="min-w-[130px]">
          <label htmlFor="pc-category" className="mb-1 block text-xs text-muted">Category</label>
          <select id="pc-category" className={selectClass} value={category} onChange={(e) => setCategory(e.target.value)}>
            {CATEGORY_OPTIONS.map((c) => (
              <option key={c} value={c}>{c.charAt(0).toUpperCase() + c.slice(1)}</option>
            ))}
          </select>
        </div>

        <div className="flex-1 min-w-[200px]">
          <label htmlFor="pc-query" className="mb-1 block text-xs text-muted">Search Query</label>
          <input
            id="pc-query"
            className={selectClass}
            placeholder="e.g. AI regulation, climate summit..."
            value={query}
            onChange={(e) => setQuery(e.target.value)}
          />
        </div>

        <div className="w-20">
          <label htmlFor="pc-max" className="mb-1 block text-xs text-muted">Max</label>
          <input
            id="pc-max"
            type="number"
            className={selectClass}
            value={maxArticles}
            min={1}
            max={20}
            onChange={(e) => setMaxArticles(Number(e.target.value))}
          />
        </div>

        <label className="flex items-center gap-2 text-xs text-muted cursor-pointer pb-2">
          <input
            type="checkbox"
            checked={generateMedia}
            onChange={(e) => setGenerateMedia(e.target.checked)}
            className="accent-indigo-500"
          />
          Media
        </label>

        <Button onClick={runPipeline} loading={running}>
          <Rocket className="h-4 w-4" aria-hidden />
          {running ? "Running..." : "Run Pipeline"}
        </Button>
      </div>

      {/* Pipeline Steps */}
      <div className="mt-4 flex flex-wrap items-center gap-1 text-xs">
        {PIPELINE_STEPS.map((step, i) => (
          <span key={step.key} className="flex items-center gap-1">
            <span
              className={`rounded px-2 py-0.5 ${
                i < currentStep
                  ? "bg-emerald-500/20 text-emerald-400"
                  : i === currentStep
                  ? "bg-indigo-500/20 text-indigo-400 animate-pulse"
                  : "bg-white/5 text-muted"
              }`}
            >
              {step.label}
            </span>
            {i < PIPELINE_STEPS.length - 1 && <span className="text-muted">→</span>}
          </span>
        ))}
      </div>

      {/* Progress Bar */}
      <div className="mt-3 h-1 w-full overflow-hidden rounded-full bg-white/5">
        <motion.div
          className="h-full bg-gradient-to-r from-indigo-500 to-cyan-500"
          initial={{ width: "0%" }}
          animate={{ width: currentStep >= 0 ? `${((currentStep + 1) / PIPELINE_STEPS.length) * 100}%` : "0%" }}
        />
      </div>
    </motion.section>
  );
}
