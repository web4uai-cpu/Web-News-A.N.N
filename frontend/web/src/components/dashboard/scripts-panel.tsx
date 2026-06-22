"use client";

import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { useDashboardStore } from "@/lib/store";
import { useToastStore } from "@/components/ui/toast";
import { api } from "@/lib/api";
import { Copy, Mic, RefreshCw } from "lucide-react";
import { useQueryClient } from "@tanstack/react-query";

export function ScriptsPanel() {
  const scripts = useDashboardStore((s) => s.scripts);
  const queryClient = useQueryClient();

  return (
    <section>
      <div className="mb-3 flex items-center justify-between">
        <h2 className="flex items-center gap-2 text-sm font-semibold">📝 Broadcast Scripts</h2>
        <button
          onClick={() => queryClient.invalidateQueries({ queryKey: ["scripts"] })}
          className="flex items-center gap-1 rounded-lg border border-white/10 bg-white/5 px-2 py-1 text-xs text-muted hover:bg-white/10"
        >
          <RefreshCw className="h-3 w-3" /> Refresh
        </button>
      </div>

      <div className="max-h-[500px] space-y-3 overflow-y-auto pr-1">
        <AnimatePresence>
          {scripts.length === 0 ? (
            <div className="rounded-xl border border-white/5 bg-white/[0.02] p-8 text-center">
              <div className="text-3xl">📡</div>
              <div className="mt-2 text-sm font-medium">No Scripts Yet</div>
              <div className="mt-1 text-xs text-muted">Run the pipeline to generate broadcast scripts.</div>
            </div>
          ) : (
            scripts.map((script, i) => (
              <ScriptCard key={script.id} script={script} index={i} />
            ))
          )}
        </AnimatePresence>
      </div>
    </section>
  );
}

function ScriptCard({ script, index }: { script: any; index: number }) {
  const [lang, setLang] = useState<"en" | "hi">("en");
  const toast = useToastStore((s) => s.add);

  const copy = () => {
    navigator.clipboard.writeText(script.english_script);
    toast("Script copied!", "success");
  };

  const genAudio = async () => {
    toast("Audio generation started...", "info");
    try {
      const result = await api.generateAudio(script.id);
      toast(result.status === "completed" ? "Audio generated!" : `Audio: ${result.status}`, "success");
    } catch (e: any) {
      toast(`Audio failed: ${e.message}`, "error");
    }
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0 }}
      transition={{ delay: index * 0.05 }}
      className="rounded-xl border border-white/5 bg-white/[0.02] p-4"
    >
      <div className="flex items-start justify-between gap-2">
        <h3 className="text-sm font-medium leading-tight">{script.headline}</h3>
        <span className="shrink-0 rounded-full bg-indigo-500/15 px-2 py-0.5 text-[10px] font-medium text-indigo-400">
          {script.category}
        </span>
      </div>

      <div className="mt-2 flex gap-1">
        <button
          onClick={() => setLang("en")}
          className={`rounded px-2 py-0.5 text-[10px] font-medium ${
            lang === "en" ? "bg-indigo-500/20 text-indigo-400" : "text-muted hover:text-white"
          }`}
        >
          🇬🇧 English
        </button>
        <button
          onClick={() => setLang("hi")}
          className={`rounded px-2 py-0.5 text-[10px] font-medium ${
            lang === "hi" ? "bg-indigo-500/20 text-indigo-400" : "text-muted hover:text-white"
          }`}
        >
          🇮🇳 Hindi
        </button>
      </div>

      <p className="mt-2 line-clamp-3 text-xs leading-relaxed text-muted">
        {lang === "hi" ? script.hindi_script : script.english_script}
      </p>

      <div className="mt-3 flex items-center justify-between">
        <div className="flex gap-3 text-[10px] text-muted">
          <span>📝 {script.word_count_en} words</span>
          <span>⏱️ ~{script.estimated_duration_seconds}s</span>
        </div>
        <div className="flex gap-1">
          <button onClick={copy} className="rounded p-1 text-muted hover:bg-white/10 hover:text-white">
            <Copy className="h-3.5 w-3.5" />
          </button>
          <button onClick={genAudio} className="rounded p-1 text-muted hover:bg-white/10 hover:text-white">
            <Mic className="h-3.5 w-3.5" />
          </button>
        </div>
      </div>
    </motion.div>
  );
}
