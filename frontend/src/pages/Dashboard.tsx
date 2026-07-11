import { useEffect, useRef } from "react";
import { Loader2, TriangleAlert } from "lucide-react";
import { useDashboard } from "@/hooks/useDashboard";
import { useLiveFeed } from "@/hooks/useLiveFeed";
import { KpiCards } from "@/components/dashboard/KpiCards";
import { FraudHeatmap } from "@/components/dashboard/FraudHeatmap";
import { RiskDistribution } from "@/components/dashboard/RiskDistribution";
import { LiveFeed } from "@/components/dashboard/LiveFeed";
import { TopRiskCustomers } from "@/components/dashboard/TopRiskCustomers";
import { RecentAlerts } from "@/components/dashboard/RecentAlerts";

export function Dashboard() {
  const { stats, loading, error } = useDashboard();
  const feed = useLiveFeed();

  // Live delta for "today's transactions": reset the baseline every time the
  // polled stats refresh (which already include the persisted live txns), then
  // add anything streamed since — so the KPI ticks up without double counting.
  const baseline = useRef(0);
  useEffect(() => {
    baseline.current = feed.totalSeen;
  }, [stats]);
  const liveToday = stats
    ? stats.todays_transactions + Math.max(0, feed.totalSeen - baseline.current)
    : 0;

  if (loading && !stats) {
    return (
      <div className="grid h-[60vh] place-items-center text-white/40">
        <div className="flex flex-col items-center gap-3">
          <Loader2 className="animate-spin text-gold-500" size={28} />
          <span className="text-sm">Loading dashboard…</span>
        </div>
      </div>
    );
  }

  if (error && !stats) {
    return (
      <div className="mx-auto mt-10 max-w-md">
        <div className="card flex flex-col items-center gap-3 p-8 text-center">
          <TriangleAlert className="text-risk-high" size={28} />
          <div className="text-sm font-medium text-white/80">
            Couldn&apos;t reach the API
          </div>
          <p className="text-xs text-white/40">{error}</p>
          <p className="text-xs text-white/40">
            Make sure the backend is running on{" "}
            <span className="text-gold-400">http://localhost:8000</span>.
          </p>
        </div>
      </div>
    );
  }

  if (!stats) return null;

  return (
    <div className="space-y-4">
      <KpiCards stats={stats} liveToday={liveToday} />

      <div className="grid grid-cols-1 items-stretch gap-4 lg:grid-cols-12">
        <div className="lg:col-span-8">
          <FraudHeatmap stats={stats} livePoints={feed.transactions} />
        </div>
        <div className="lg:col-span-4">
          <RiskDistribution stats={stats} />
        </div>
      </div>

      <div className="grid grid-cols-1 gap-4 lg:grid-cols-3">
        <LiveFeed feed={feed} />
        <TopRiskCustomers stats={stats} />
        <RecentAlerts stats={stats} />
      </div>
    </div>
  );
}
