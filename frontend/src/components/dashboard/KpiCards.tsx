import { Link } from "react-router-dom";
import { motion } from "framer-motion";
import {
  Activity,
  CheckCircle2,
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
  to?: string;
  accent?: string;
}

export function KpiCards({ stats }: { stats: DashboardStats }) {
  const items: Kpi[] = [
    { label: "Total Customers", value: stats.total_customers, icon: Users, to: "/customers" },
    { label: "Today's Transactions", value: stats.todays_transactions, icon: Activity },
    { label: "Open Cases", value: stats.open_cases, icon: FolderOpen, to: "/cases/open" },
    {
      label: "Closed Cases",
      value: stats.closed_cases,
      icon: CheckCircle2,
      to: "/cases/closed",
      accent: "#34d399",
    },
  ];

  return (
    <div className="grid grid-cols-2 gap-4 lg:grid-cols-4">
      {items.map((kpi, i) => {
        const accent = kpi.accent ?? "#d4af37";
        const card = (
          <motion.div
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.35, delay: i * 0.05 }}
            className={cn(
              "card relative h-full overflow-hidden p-5",
              kpi.to && "card-hover cursor-pointer",
            )}
          >
            <div className="flex items-start justify-between">
              <span className="stat-label">{kpi.label}</span>
              <span
                className="grid h-8 w-8 place-items-center rounded-lg"
                style={{ backgroundColor: `${accent}1f`, color: accent }}
              >
                <kpi.icon size={16} />
              </span>
            </div>
            <div className="mt-3 text-3xl font-bold tracking-tight tabular-nums text-white">
              <AnimatedNumber value={kpi.value} />
            </div>
            {kpi.to && (
              <div className="mt-1 text-xs text-white/35">View all →</div>
            )}
            <div
              className="pointer-events-none absolute -right-6 -top-6 h-20 w-20 rounded-full blur-2xl"
              style={{ backgroundColor: `${accent}1a` }}
            />
          </motion.div>
        );
        return kpi.to ? (
          <Link key={kpi.label} to={kpi.to}>
            {card}
          </Link>
        ) : (
          <div key={kpi.label}>{card}</div>
        );
      })}
    </div>
  );
}
