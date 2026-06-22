"use client";

import { useMemo } from "react";
import { AreaChart, Area, XAxis, YAxis, Tooltip, ResponsiveContainer, PieChart, Pie, Cell } from "recharts";
import { DollarSign, TrendingUp, Users, CreditCard, ArrowUpRight, ArrowDownRight } from "lucide-react";

const MONTHLY_REVENUE = [
  { month: "Jan", revenue: 1200, api: 800, ads: 300, subs: 100 },
  { month: "Feb", revenue: 1800, api: 1100, ads: 450, subs: 250 },
  { month: "Mar", revenue: 2400, api: 1500, ads: 550, subs: 350 },
  { month: "Apr", revenue: 3800, api: 2200, ads: 800, subs: 800 },
  { month: "May", revenue: 5200, api: 3000, ads: 1000, subs: 1200 },
  { month: "Jun", revenue: 7400, api: 4200, ads: 1200, subs: 2000 },
];

const STREAM_BREAKDOWN = [
  { name: "Enterprise API", value: 4200, color: "#8b5cf6" },
  { name: "Advertising", value: 1200, color: "#06b6d4" },
  { name: "Subscriptions", value: 2000, color: "#10b981" },
];

export function RevenuePanel() {
  const currentMonth = MONTHLY_REVENUE[MONTHLY_REVENUE.length - 1];
  const prevMonth = MONTHLY_REVENUE[MONTHLY_REVENUE.length - 2];
  const growthPct = ((currentMonth.revenue - prevMonth.revenue) / prevMonth.revenue * 100).toFixed(0);
  const isGrowth = Number(growthPct) >= 0;

  const kpis = useMemo(() => [
    {
      label: "MRR",
      value: `$${(currentMonth.revenue).toLocaleString()}`,
      change: `${isGrowth ? "+" : ""}${growthPct}%`,
      positive: isGrowth,
      Icon: DollarSign,
      color: "text-emerald-400",
    },
    {
      label: "B2B Clients",
      value: "23",
      change: "+3 this month",
      positive: true,
      Icon: Users,
      color: "text-violet-400",
    },
    {
      label: "API Revenue",
      value: `$${currentMonth.api.toLocaleString()}`,
      change: `${((currentMonth.api - prevMonth.api) / prevMonth.api * 100).toFixed(0)}% growth`,
      positive: true,
      Icon: CreditCard,
      color: "text-cyan-400",
    },
    {
      label: "ARR",
      value: `$${(currentMonth.revenue * 12).toLocaleString()}`,
      change: "run rate",
      positive: true,
      Icon: TrendingUp,
      color: "text-blue-400",
    },
  ], []);

  return (
    <div className="rounded-xl border border-white/5 bg-white/[0.02] p-5 backdrop-blur-sm">
      <div className="mb-4 flex items-center justify-between">
        <h2 className="flex items-center gap-2 text-sm font-semibold">
          <DollarSign className="h-4 w-4 text-emerald-400" />
          Revenue
        </h2>
        <span className="text-[10px] text-muted">Last 6 months</span>
      </div>

      {/* KPI Cards */}
      <div className="mb-4 grid grid-cols-2 gap-2 lg:grid-cols-4">
        {kpis.map((kpi) => (
          <div key={kpi.label} className="rounded-lg bg-white/5 p-2.5">
            <div className="flex items-center gap-1 text-[10px] text-muted">
              <kpi.Icon className={`h-3 w-3 ${kpi.color}`} />
              {kpi.label}
            </div>
            <div className="mt-1 text-base font-bold">{kpi.value}</div>
            <div className={`flex items-center gap-0.5 text-[9px] ${kpi.positive ? "text-emerald-400" : "text-red-400"}`}>
              {kpi.positive ? <ArrowUpRight className="h-2.5 w-2.5" /> : <ArrowDownRight className="h-2.5 w-2.5" />}
              {kpi.change}
            </div>
          </div>
        ))}
      </div>

      {/* Revenue Chart + Pie */}
      <div className="grid gap-4 lg:grid-cols-[2fr_1fr]">
        {/* Area Chart */}
        <div>
          <div className="mb-2 text-[10px] font-semibold text-muted">Monthly Revenue Trend</div>
          <div className="h-40">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={MONTHLY_REVENUE} margin={{ top: 5, right: 5, left: -20, bottom: 0 }}>
                <defs>
                  <linearGradient id="revGrad" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="0%" stopColor="#10b981" stopOpacity={0.3} />
                    <stop offset="100%" stopColor="#10b981" stopOpacity={0} />
                  </linearGradient>
                </defs>
                <XAxis
                  dataKey="month"
                  tick={{ fontSize: 9, fill: "#64748b" }}
                  axisLine={false}
                  tickLine={false}
                />
                <YAxis
                  tick={{ fontSize: 9, fill: "#64748b" }}
                  axisLine={false}
                  tickLine={false}
                  tickFormatter={(v) => `$${v >= 1000 ? `${(v / 1000).toFixed(0)}K` : v}`}
                />
                <Tooltip
                  contentStyle={{ background: "#0f0f1e", border: "1px solid rgba(255,255,255,0.1)", borderRadius: 8, fontSize: 11 }}
                  formatter={(value) => [`$${Number(value).toLocaleString()}`, "Revenue"]}
                />
                <Area type="monotone" dataKey="revenue" stroke="#10b981" strokeWidth={2} fill="url(#revGrad)" />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Pie Chart — Revenue Streams */}
        <div>
          <div className="mb-2 text-[10px] font-semibold text-muted">Revenue Streams</div>
          <div className="h-32">
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie
                  data={STREAM_BREAKDOWN}
                  cx="50%"
                  cy="50%"
                  innerRadius={30}
                  outerRadius={50}
                  paddingAngle={3}
                  dataKey="value"
                >
                  {STREAM_BREAKDOWN.map((entry) => (
                    <Cell key={entry.name} fill={entry.color} />
                  ))}
                </Pie>
                <Tooltip
                  contentStyle={{ background: "#0f0f1e", border: "1px solid rgba(255,255,255,0.1)", borderRadius: 8, fontSize: 11 }}
                  formatter={(value) => [`$${Number(value).toLocaleString()}`, ""]}
                />
              </PieChart>
            </ResponsiveContainer>
          </div>
          <div className="space-y-1">
            {STREAM_BREAKDOWN.map((s) => (
              <div key={s.name} className="flex items-center justify-between text-[9px]">
                <div className="flex items-center gap-1.5">
                  <span className="h-2 w-2 rounded-full" style={{ background: s.color }} />
                  <span className="text-muted">{s.name}</span>
                </div>
                <span className="font-medium">${s.value.toLocaleString()}</span>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
