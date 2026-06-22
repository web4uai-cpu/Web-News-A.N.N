"use client";

import { useState } from "react";
import { useForm } from "react-hook-form";
import { motion, AnimatePresence } from "framer-motion";
import { useToastStore } from "@/components/ui/toast";
import { Sparkles, Cpu, Database, Mic, CheckCircle, PlayCircle, Download, Send } from "lucide-react";

type StudioPhase = "idle" | "synthesizing" | "scraping" | "rendering" | "complete";

const PHASES: Record<StudioPhase, { icon: typeof Cpu; color: string; text: string; sub: string } | null> = {
  idle: null,
  synthesizing: { icon: Cpu, color: "text-violet-500 border-violet-500/30", text: "Synthesizing AI Engine", sub: "Allocating 50 Enterprise Quota Credits." },
  scraping: { icon: Database, color: "text-cyan-500 border-cyan-500/30", text: "Scraping Global Reality", sub: "Parsing 40,000 global node events." },
  rendering: { icon: Mic, color: "text-rose-500 border-rose-500/30", text: "Rendering Avatar Video", sub: "Pushing payload to GPU cluster." },
  complete: null,
};

export function StudioTab() {
  const { register, handleSubmit, watch } = useForm<{
    niche: string;
    tone: string;
    topic: string;
    script: string;
  }>();
  const toast = useToastStore((s) => s.add);
  const [phase, setPhase] = useState<StudioPhase>("idle");
  const topic = watch("topic");

  const onSubmit = handleSubmit(async (data) => {
    if (!data.topic) {
      toast("Please input a target prompt", "warning");
      return;
    }
    setPhase("synthesizing");
    await delay(3000);
    setPhase("scraping");
    await delay(3500);
    setPhase("rendering");
    await delay(4000);
    setPhase("complete");
    toast("Broadcast synthesis complete!", "success");
  });

  const inputClass =
    "w-full rounded-2xl border border-white/10 bg-black/60 px-4 py-3 text-sm text-white placeholder:text-white/30 outline-none focus:border-cyan-500 focus:shadow-[0_0_20px_rgba(6,182,212,0.3)] transition-all";
  const selectClass = `${inputClass} appearance-none cursor-pointer`;

  return (
    <section className="rounded-[30px] border border-violet-500/20 bg-gradient-to-br from-violet-500/5 to-cyan-500/5 p-8">
      <div className="mb-8 text-center">
        <h2 className="text-2xl font-black">Autonomous Studio Synthesizer</h2>
        <p className="mt-2 text-sm text-muted">
          Configure parameters for your next AI Broadcast. The Matrix auto-publishes upon completion.
        </p>
      </div>

      <form
        onSubmit={onSubmit}
        className="mx-auto max-w-3xl rounded-3xl border border-white/5 bg-black/40 p-8 space-y-6"
      >
        <div className="grid gap-6 sm:grid-cols-2">
          <div>
            <label className="mb-2 flex items-center gap-1.5 text-xs font-semibold text-muted">
              Content Niche
            </label>
            <select {...register("niche")} className={selectClass}>
              <option value="technology">Technology & AI</option>
              <option value="finance">Finance & Markets</option>
              <option value="crypto">Cryptocurrency</option>
              <option value="global">Global Events</option>
              <option value="entertainment">Pop Culture</option>
            </select>
          </div>
          <div>
            <label className="mb-2 flex items-center gap-1.5 text-xs font-semibold text-muted">
              Presenter Tone
            </label>
            <select {...register("tone")} className={selectClass}>
              <option value="professional">Professional / News Anchor</option>
              <option value="dramatic">Dramatic / Breaking</option>
              <option value="casual">Casual / Influencer</option>
            </select>
          </div>
        </div>

        <div>
          <label className="mb-2 block text-xs font-semibold text-muted">Subject / Target Prompt</label>
          <input
            {...register("topic")}
            placeholder="e.g., 'Apple announces new VR headset'"
            className={inputClass}
          />
        </div>

        <div>
          <label className="mb-2 flex items-center justify-between text-xs font-semibold text-muted">
            <span>Direct Script Override (Optional)</span>
            <span className="text-white/20">Leave blank for Auto-AI Gen</span>
          </label>
          <textarea
            {...register("script")}
            rows={3}
            placeholder="Paste your exact script to bypass AI generation..."
            className={`${inputClass} resize-y`}
          />
        </div>

        <button
          type="submit"
          disabled={phase !== "idle" && phase !== "complete"}
          className="flex w-full items-center justify-center gap-2 rounded-2xl bg-gradient-to-r from-violet-600 to-purple-700 py-4 text-lg font-bold text-white uppercase tracking-wider hover:shadow-lg hover:shadow-violet-500/30 transition-all disabled:opacity-50"
        >
          <Sparkles className="h-5 w-5" /> Execute Synthesis
        </button>
      </form>

      {/* Status Area */}
      <AnimatePresence mode="wait">
        {phase !== "idle" && phase !== "complete" && PHASES[phase] && (
          <motion.div
            key={phase}
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0 }}
            className={`mx-auto mt-8 max-w-3xl rounded-2xl border bg-black/50 p-8 text-center ${PHASES[phase]!.color}`}
          >
            {(() => {
              const Icon = PHASES[phase]!.icon;
              return <Icon className="mx-auto h-12 w-12 animate-spin" />;
            })()}
            <h3 className="mt-4 text-xl font-black text-white">
              {PHASES[phase]!.text} for &ldquo;{topic}&rdquo;...
            </h3>
            <p className="mt-1 text-sm text-muted">{PHASES[phase]!.sub}</p>
          </motion.div>
        )}

        {phase === "complete" && (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="mx-auto mt-8 max-w-3xl rounded-3xl border border-emerald-500/30 bg-emerald-500/5 p-8 text-center"
          >
            <h3 className="flex items-center justify-center gap-2 text-xl font-black text-emerald-400">
              <CheckCircle className="h-7 w-7" /> Broadcast Synthesis Complete!
            </h3>
            <p className="mt-2 text-sm text-muted">
              Target Topic: <strong className="text-white">&ldquo;{topic}&rdquo;</strong>
            </p>

            <div className="mx-auto my-6 flex h-64 w-full items-center justify-center rounded-2xl border border-white/10 bg-black">
              <PlayCircle className="h-16 w-16 text-emerald-400 opacity-60" />
            </div>

            <div className="flex justify-center gap-4">
              <button
                onClick={() => toast("MP4 Download Triggered", "info")}
                className="flex items-center gap-2 rounded-2xl bg-emerald-500 px-6 py-3 font-bold text-white"
              >
                <Download className="h-4 w-4" /> Download .MP4
              </button>
              <button
                onClick={() => { toast("Pushed to social network queue!", "success"); setPhase("idle"); }}
                className="flex items-center gap-2 rounded-2xl bg-gradient-to-r from-pink-500 to-indigo-500 px-6 py-3 font-bold text-white"
              >
                <Send className="h-4 w-4" /> Distribute to Nodes
              </button>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </section>
  );
}

function delay(ms: number) {
  return new Promise((r) => setTimeout(r, ms));
}

function toast(msg: string, type: "info" | "success" | "warning") {
  useToastStore.getState().add(msg, type);
}
