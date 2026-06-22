"use client";

import { useState } from "react";
import { motion } from "framer-motion";
import { useAuthStore } from "@/lib/auth-store";
import { Loader2 } from "lucide-react";

type Mode = "login" | "signup" | "reset";

export function LoginScreen() {
  const { signIn, signUp, resetPassword, error, clearError } = useAuthStore();
  const [mode, setMode] = useState<Mode>("login");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [submitting, setSubmitting] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setSubmitting(true);
    if (mode === "login") await signIn(email, password);
    else if (mode === "signup") await signUp(email, password);
    else await resetPassword(email);
    setSubmitting(false);
  };

  const switchMode = (m: Mode) => {
    clearError();
    setMode(m);
  };

  const inputClass =
    "w-full rounded-2xl border border-white/10 bg-black/40 px-5 py-4 text-base text-white placeholder:text-white/30 outline-none focus:border-violet-500 focus:shadow-[0_0_20px_rgba(139,92,246,0.3)] transition-all";

  return (
    <div className="flex min-h-screen items-center justify-center">
      <motion.div
        animate={{ y: [0, -15, 0] }}
        transition={{ duration: 6, repeat: Infinity, ease: "easeInOut" }}
        className="relative w-full max-w-md rounded-[30px] border border-white/10 bg-panel p-10 text-center shadow-2xl backdrop-blur-xl"
      >
        <div className="absolute -inset-px rounded-[31px] bg-gradient-to-br from-violet-500/30 via-transparent to-cyan-500/30 -z-10" />

        <h1 className="bg-gradient-to-r from-white to-muted bg-clip-text text-4xl font-black tracking-tight text-transparent">
          A.N.N. Hub
        </h1>
        <p className="mt-2 text-muted">Secure Enterprise Orbital Access</p>

        <form onSubmit={handleSubmit} className="mt-8 space-y-4">
          <input
            type="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            placeholder="Corporate Email"
            required
            className={inputClass}
          />
          {mode !== "reset" && (
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="Passphrase"
              required
              className={inputClass}
            />
          )}

          <button
            type="submit"
            disabled={submitting}
            className="flex w-full items-center justify-center gap-2 rounded-2xl bg-gradient-to-r from-violet-600 to-purple-700 py-4 text-lg font-bold text-white uppercase tracking-wider hover:shadow-lg hover:shadow-violet-500/30 transition-all disabled:opacity-50"
          >
            {submitting && <Loader2 className="h-5 w-5 animate-spin" />}
            {mode === "login" && "Secure Logon"}
            {mode === "signup" && "Deploy Instance"}
            {mode === "reset" && "Transmit Reset Link"}
          </button>
        </form>

        {error && (
          <div className="mt-4 text-sm text-red-400">{error}</div>
        )}

        <div className="mt-5 flex flex-col gap-3">
          {mode === "login" && (
            <>
              <button onClick={() => switchMode("signup")} className="text-sm text-cyan-400 hover:text-white transition-colors">
                Deploy New Account Instance
              </button>
              <button onClick={() => switchMode("reset")} className="text-xs text-muted hover:text-white transition-colors">
                Forgot Passphrase?
              </button>
            </>
          )}
          {mode === "signup" && (
            <button onClick={() => switchMode("login")} className="text-sm text-cyan-400 hover:text-white transition-colors">
              Connect to Existing Instance
            </button>
          )}
          {mode === "reset" && (
            <button onClick={() => switchMode("login")} className="text-sm text-cyan-400 hover:text-white transition-colors">
              Abort Reset
            </button>
          )}
        </div>
      </motion.div>
    </div>
  );
}
