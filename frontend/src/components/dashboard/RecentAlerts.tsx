import { Link } from "react-router-dom";
import { Bell } from "lucide-react";
import { Panel } from "@/components/ui/Card";
import { Badge } from "@/components/ui/Badge";
import { RISK_COLORS } from "@/components/ui/RiskBadge";
import { relativeTime } from "@/lib/format";
import type { DashboardStats } from "@/types/api";

export function RecentAlerts({ stats }: { stats: DashboardStats }) {
  const alerts = stats.recent_alerts.slice(0, 6);

  return (
    <Panel title="Recent Alerts" icon={<Bell size={16} />} bodyClassName="p-3">
      {alerts.length === 0 ? (
        <p className="p-4 text-sm text-white/40">No alerts yet.</p>
      ) : (
        <ul className="divide-y divide-white/5">
          {alerts.map((a) => (
            <li key={a.id}>
              <Link
                to={`/investigations/${a.customer_id}`}
                className="flex gap-3 rounded-lg px-2 py-2.5 transition-colors hover:bg-white/5"
              >
                <span
                  className="mt-1.5 h-2 w-2 shrink-0 rounded-full"
                  style={{ backgroundColor: RISK_COLORS[a.severity] }}
                />
                <div className="min-w-0 flex-1">
                  <div className="truncate text-sm font-medium text-white/90">
                    {a.title}
                  </div>
                  <div className="mt-1 flex flex-wrap items-center gap-1.5">
                    {a.triggered_rules.slice(0, 3).map((r) => (
                      <Badge
                        key={r}
                        className="border-white/10 bg-white/5 text-white/50"
                      >
                        {r}
                      </Badge>
                    ))}
                    <span className="text-[11px] text-white/30">
                      {relativeTime(a.created_at)}
                    </span>
                  </div>
                </div>
                <span className="shrink-0 text-sm font-bold tabular-nums text-white/70">
                  {a.score}
                </span>
              </Link>
            </li>
          ))}
        </ul>
      )}
    </Panel>
  );
}
