"use client";

import { AreaChart, Area, XAxis, YAxis, Tooltip, ResponsiveContainer, BarChart, Bar } from "recharts";
import { Newspaper, TrendingUp, Globe, Zap } from "lucide-react";
import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api";

export function NewsThroughput() {
  const { data } = useQuery({
    queryKey: ["dashboard-throughput"],
    queryFn: () => api.dashboardThroughput(),
    refetchInterval: 30000,
  });

  const hourlyData = data?.hourly ?? [];
  const categoryBreakdown = data?.categories ?? [];
  const totalToday = data?.total_today ?? 0;
  const avgPerHour = data?.avg_per_hour ?? 0;

  return (
    <div className="rounded-xl border border-white/5 bg-white/[0.02] p-5 backdrop-blur-sm">
      <div className="mb-4 flex items-center justify-between">
        <h2 className="flex items-center gap-2 text-sm font-semibold">
          <Newspaper className="h-4 w-4 text-blue-400" />
          News Throughput
        </h2>
        <span className="text-[10px] text-muted">Last 24 hours</span>
      </div>

      <div className="mb-4 grid grid-cols-3 gap-3">
        {[
          { label: "Total Today", value: totalToday.toString(), Icon: TrendingUp, color: "text-blue-400" },
          { label: "Avg/Hour", value: avgPerHour.toFixed(1), Icon: Zap, color: "text-cyan-400" },
          { label: "Languages", value: "5", Icon: Globe, color: "text-violet-400" },
        ].map((kpi) => (
          <div key={kpi.label} className="rounded-lg bg-white/5 p-2.5 text-center">
            <kpi.Icon className={`mx-auto h-3.5 w-3.5 ${kpi.color}`} />
            <div className="mt-1 text-lg font-bold">{kpi.value}</div>
            <div className="text-[9px] text-muted">{kpi.label}</div>
          </div>
        ))}
      </div>

      <div className="h-36">
        <ResponsiveContainer width="100%" height="100%">
          <AreaChart data={hourlyData} margin={{ top: 5, right: 5, left: -20, bottom: 0 }}>
            <defs>
              <linearGradient id="throughputGrad" x1="0" y1="0" x2="0" y2="1">
                <stop offset="0%" stopColor="#3b82f6" stopOpacity={0.3} />
                <stop offset="100%" stopColor="#3b82f6" stopOpacity={0} />
              </linearGradient>
            </defs>
            <XAxis
              dataKey="hour"
              tick={{ fontSize: 9, fill: "#64748b" }}
              axisLine={false}
              tickLine={false}
              interval={5}
            />
            <YAxis tick={{ fontSize: 9, fill: "#64748b" }} axisLine={false} tickLine={false} />
            <Tooltip
              contentStyle={{ background: "#0f0f1e", border: "1px solid rgba(255,255,255,0.1)", borderRadius: 8, fontSize: 11 }}
              labelStyle={{ color: "#94a3b8" }}
            />
            <Area
              type="monotone"
              dataKey="articles"
              stroke="#3b82f6"
              strokeWidth={2}
              fill="url(#throughputGrad)"
            />
          </AreaChart>
        </ResponsiveContainer>
      </div>

      <div className="mt-4 border-t border-white/5 pt-3">
        <div className="mb-2 text-[10px] font-semibold text-muted">Category Distribution</div>
        <div className="h-24">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={categoryBreakdown} margin={{ top: 0, right: 0, left: -20, bottom: 0 }}>
              <XAxis
                dataKey="category"
                tick={{ fontSize: 8, fill: "#64748b" }}
                axisLine={false}
                tickLine={false}
              />
              <YAxis tick={{ fontSize: 8, fill: "#64748b" }} axisLine={false} tickLine={false} />
              <Tooltip
                contentStyle={{ background: "#0f0f1e", border: "1px solid rgba(255,255,255,0.1)", borderRadius: 8, fontSize: 11 }}
              />
              <Bar
                dataKey="count"
                radius={[4, 4, 0, 0]}
                fill="#3b82f6"
              />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>
    </div>
  );
}
