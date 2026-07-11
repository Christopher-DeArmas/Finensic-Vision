import { useState } from "react";
import { Cell, Pie, PieChart, ResponsiveContainer } from "recharts";
import { Globe, ShieldAlert } from "lucide-react";
import { Panel } from "@/components/ui/Card";
import { RISK_COLORS } from "@/components/ui/RiskBadge";
import type { DashboardStats, RiskLevel } from "@/types/api";

const ORDER: RiskLevel[] = ["critical", "high", "medium", "low"];

export function RiskDistribution({ stats }: { stats: DashboardStats }) {
  const [active, setActive] = useState<number | null>(null);
  const dist = stats.risk_distribution;
  const total = ORDER.reduce((sum, k) => sum + (dist[k] ?? 0), 0);
  const data = ORDER.map((level) => ({
    level,
    value: dist[level] ?? 0,
    color: RISK_COLORS[level],
  })).filter((d) => d.value > 0);

  const regions = stats.top_regions ?? [];
  const maxRegion = Math.max(1, ...regions.map((r) => r.count));

  return (
    <Panel title="Risk Distribution" icon={<ShieldAlert size={16} />}>
      <div className="flex items-center gap-5">
        <div className="relative h-36 w-36 shrink-0">
          <ResponsiveContainer width="100%" height="100%">
            <PieChart>
              <Pie
                data={data}
                dataKey="value"
                nameKey="level"
                innerRadius={48}
                outerRadius={64}
                paddingAngle={2}
                stroke="none"
                startAngle={90}
                endAngle={-270}
                onMouseEnter={(_, i) => setActive(i)}
                onMouseLeave={() => setActive(null)}
              >
                {data.map((d, i) => (
                  <Cell
                    key={d.level}
                    fill={d.color}
                    fillOpacity={active === null || active === i ? 1 : 0.3}
                    stroke={active === i ? d.color : "none"}
                    strokeWidth={active === i ? 2 : 0}
                    style={{ transition: "fill-opacity 0.15s", cursor: "pointer" }}
                  />
                ))}
              </Pie>
            </PieChart>
          </ResponsiveContainer>
          <div className="pointer-events-none absolute inset-0 flex flex-col items-center justify-center">
            <span
              className="text-2xl font-bold tabular-nums"
              style={{ color: active !== null ? data[active].color : "#fff" }}
            >
              {active !== null ? data[active].value : total}
            </span>
            <span className="text-[10px] uppercase capitalize tracking-wider text-white/40">
              {active !== null ? data[active].level : "Customers"}
            </span>
          </div>
        </div>

        <ul className="flex-1 space-y-2">
          {ORDER.map((level) => (
            <li key={level} className="flex items-center justify-between text-sm">
              <span className="flex items-center gap-2">
                <span
                  className="h-2.5 w-2.5 rounded-sm"
                  style={{ backgroundColor: RISK_COLORS[level] }}
                />
                <span className="capitalize text-white/70">{level}</span>
              </span>
              <span className="font-semibold tabular-nums text-white/90">
                {dist[level] ?? 0}
              </span>
            </li>
          ))}
        </ul>
      </div>

      <div className="mt-5 border-t border-white/5 pt-4">
        <div className="stat-label mb-3 flex items-center gap-1.5">
          <Globe size={12} /> Common Risky Regions
        </div>
        {regions.length === 0 ? (
          <p className="text-sm text-white/40">No flagged activity yet.</p>
        ) : (
          <ul className="space-y-2.5">
            {regions.map((r) => (
              <li key={r.region}>
                <div className="mb-1 flex items-center justify-between text-xs">
                  <span className="text-white/70">{r.region}</span>
                  <span className="tabular-nums text-white/45">
                    {r.count} flagged
                  </span>
                </div>
                <div className="h-2 w-full overflow-hidden rounded-full bg-white/5">
                  <div
                    className="h-full rounded-full bg-brand-500"
                    style={{ width: `${(r.count / maxRegion) * 100}%` }}
                  />
                </div>
              </li>
            ))}
          </ul>
        )}
      </div>
    </Panel>
  );
}
