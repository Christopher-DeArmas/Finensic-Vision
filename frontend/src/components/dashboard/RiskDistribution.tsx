import { Cell, Pie, PieChart, ResponsiveContainer } from "recharts";
import { ShieldAlert } from "lucide-react";
import { Panel } from "@/components/ui/Card";
import { RISK_COLORS } from "@/components/ui/RiskBadge";
import type { DashboardStats, RiskLevel } from "@/types/api";

const ORDER: RiskLevel[] = ["critical", "high", "medium", "low"];

export function RiskDistribution({ stats }: { stats: DashboardStats }) {
  const dist = stats.risk_distribution;
  const total = ORDER.reduce((sum, k) => sum + (dist[k] ?? 0), 0);
  const data = ORDER.map((level) => ({
    level,
    value: dist[level] ?? 0,
    color: RISK_COLORS[level],
  })).filter((d) => d.value > 0);

  return (
    <Panel title="Risk Distribution" icon={<ShieldAlert size={16} />}>
      <div className="flex items-center gap-5">
        <div className="relative h-40 w-40 shrink-0">
          <ResponsiveContainer width="100%" height="100%">
            <PieChart>
              <Pie
                data={data}
                dataKey="value"
                nameKey="level"
                innerRadius={52}
                outerRadius={70}
                paddingAngle={2}
                stroke="none"
                startAngle={90}
                endAngle={-270}
              >
                {data.map((d) => (
                  <Cell key={d.level} fill={d.color} />
                ))}
              </Pie>
            </PieChart>
          </ResponsiveContainer>
          <div className="pointer-events-none absolute inset-0 flex flex-col items-center justify-center">
            <span className="text-2xl font-bold tabular-nums text-white">
              {total}
            </span>
            <span className="text-[10px] uppercase tracking-wider text-white/40">
              Customers
            </span>
          </div>
        </div>

        <ul className="flex-1 space-y-2">
          {ORDER.map((level) => (
            <li
              key={level}
              className="flex items-center justify-between text-sm"
            >
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
    </Panel>
  );
}
