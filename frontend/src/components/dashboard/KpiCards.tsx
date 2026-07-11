import { motion } from "framer-motion";
import {
  Activity,
  AlertTriangle,
  FolderOpen,
  Users,
  type LucideIcon,
} from "lucide-react";
import { AnimatedNumber } from "@/components/ui/AnimatedNumber";
import { cn } from "@/lib/cn";
import type { DashboardStats } from "@/types/api";

interface Kpi {
  label: string;
  value: number;
  icon: LucideIcon;
  danger?: boolean;
  hint?: string;
}

export function KpiCards({
  stats,
  liveToday,
}: {
  stats: DashboardStats;
  liveToday?: number;
}) {
  const items: Kpi[] = [
    { label: "Total Customers", value: stats.total_customers, icon: Users },
    {
      label: "Today's Transactions",
      value: liveToday ?? stats.todays_transactions,
      icon: Activity,
      hint: `${stats.total_transactions.toLocaleString()} total`,
    },
    { label: "Open Cases", value: stats.open_cases, icon: FolderOpen },
    {
      label: "Critical Cases",
      value: stats.critical_cases,
      icon: AlertTriangle,
      danger: true,
    },
  ];

  return (
    <div className="grid grid-cols-2 gap-4 lg:grid-cols-4">
      {items.map((kpi, i) => (
        <motion.div
          key={kpi.label}
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.35, delay: i * 0.05 }}
          className="card card-hover relative overflow-hidden p-5"
        >
          <div className="flex items-start justify-between">
            <span className="stat-label">{kpi.label}</span>
            <span
              className={cn(
                "grid h-8 w-8 place-items-center rounded-lg",
                kpi.danger
                  ? "bg-risk-critical/10 text-risk-critical"
                  : "bg-gold-500/10 text-gold-400",
              )}
            >
              <kpi.icon size={16} />
            </span>
          </div>
          <div
            className={cn(
              "mt-3 text-3xl font-bold tracking-tight tabular-nums",
              kpi.danger && kpi.value > 0 ? "text-risk-critical" : "text-white",
            )}
          >
            <AnimatedNumber value={kpi.value} />
          </div>
          {kpi.hint && (
            <div className="mt-1 text-xs text-white/35">{kpi.hint}</div>
          )}
          <div className="pointer-events-none absolute -right-6 -top-6 h-20 w-20 rounded-full bg-brand-500/10 blur-2xl" />
        </motion.div>
      ))}
    </div>
  );
}
