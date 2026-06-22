"use client";

import { useEffect, useState } from "react";
import { motion } from "framer-motion";
import { TrendingUp, TrendingDown, BarChart3 } from "lucide-react";

interface MarketTicker {
  symbol: string;
  name: string;
  price: number;
  change: number;
  changePct: number;
}

const INITIAL_TICKERS: MarketTicker[] = [
  { symbol: "AAPL", name: "Apple", price: 234.56, change: 3.21, changePct: 1.39 },
  { symbol: "NVDA", name: "NVIDIA", price: 892.30, change: -12.45, changePct: -1.38 },
  { symbol: "MSFT", name: "Microsoft", price: 456.78, change: 5.67, changePct: 1.26 },
  { symbol: "GOOGL", name: "Alphabet", price: 178.90, change: 2.34, changePct: 1.33 },
  { symbol: "AMZN", name: "Amazon", price: 198.45, change: -1.23, changePct: -0.62 },
  { symbol: "TSLA", name: "Tesla", price: 267.89, change: 8.90, changePct: 3.44 },
  { symbol: "BTC", name: "Bitcoin", price: 91234.56, change: 1234.56, changePct: 1.37 },
  { symbol: "ETH", name: "Ethereum", price: 3456.78, change: -45.67, changePct: -1.30 },
];

export function LiveMarkets() {
  const [tickers, setTickers] = useState(INITIAL_TICKERS);

  useEffect(() => {
    const interval = setInterval(() => {
      setTickers((prev) =>
        prev.map((t) => {
          const delta = (Math.random() - 0.48) * t.price * 0.005;
          const newPrice = +(t.price + delta).toFixed(2);
          const newChange = +(newPrice - (t.price - t.change)).toFixed(2);
          const newPct = +((newChange / (newPrice - newChange)) * 100).toFixed(2);
          return { ...t, price: newPrice, change: newChange, changePct: newPct };
        })
      );
    }, 3000);
    return () => clearInterval(interval);
  }, []);

  return (
    <section className="border-y border-white/5 bg-[#080810]/50">
      <div className="mx-auto max-w-7xl px-4 py-5">
        <div className="mb-3 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <BarChart3 className="h-4 w-4 text-cyan-400" />
            <h2 className="text-sm font-semibold">Live Markets</h2>
            <span className="flex items-center gap-1 rounded bg-emerald-500/10 px-1.5 py-0.5 text-[9px] font-bold text-emerald-400">
              <span className="live-dot h-1 w-1 rounded-full bg-emerald-500" />
              REAL-TIME
            </span>
          </div>
          <span className="text-[10px] text-muted">Data via AlphaVantage</span>
        </div>

        <div className="grid grid-cols-2 gap-2 sm:grid-cols-4 lg:grid-cols-8">
          {tickers.map((t) => {
            const isUp = t.change >= 0;
            return (
              <motion.div
                key={t.symbol}
                layout
                className="rounded-lg border border-white/5 bg-white/[0.02] p-2.5 transition-colors hover:border-white/10"
              >
                <div className="flex items-center justify-between">
                  <span className="text-[10px] font-bold text-white/60">{t.symbol}</span>
                  {isUp ? (
                    <TrendingUp className="h-3 w-3 text-emerald-400" />
                  ) : (
                    <TrendingDown className="h-3 w-3 text-red-400" />
                  )}
                </div>
                <div className="mt-1 text-sm font-bold">
                  {t.symbol === "BTC" || t.symbol === "ETH"
                    ? `$${t.price.toLocaleString(undefined, { maximumFractionDigits: 0 })}`
                    : `$${t.price.toFixed(2)}`}
                </div>
                <div className={`mt-0.5 text-[10px] font-medium ${isUp ? "text-emerald-400" : "text-red-400"}`}>
                  {isUp ? "+" : ""}{t.changePct.toFixed(2)}%
                </div>
              </motion.div>
            );
          })}
        </div>
      </div>
    </section>
  );
}
