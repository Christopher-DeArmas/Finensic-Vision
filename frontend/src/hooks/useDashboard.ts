import { useCallback, useEffect, useRef, useState } from "react";
import { api } from "@/services/api";
import type { DashboardStats } from "@/types/api";

interface DashboardState {
  stats: DashboardStats | null;
  loading: boolean;
  error: string | null;
}

/** Fetches dashboard stats on mount and refreshes on an interval. */
export function useDashboard(refreshMs = 15_000): DashboardState {
  const [state, setState] = useState<DashboardState>({
    stats: null,
    loading: true,
    error: null,
  });
  const mounted = useRef(true);

  const load = useCallback(async () => {
    try {
      const stats = await api.dashboardStats();
      if (mounted.current) setState({ stats, loading: false, error: null });
    } catch (err) {
      if (mounted.current)
        setState((s) => ({
          ...s,
          loading: false,
          error: err instanceof Error ? err.message : "Failed to load",
        }));
    }
  }, []);

  useEffect(() => {
    mounted.current = true;
    void load();
    const id = setInterval(() => void load(), refreshMs);
    return () => {
      mounted.current = false;
      clearInterval(id);
    };
  }, [load, refreshMs]);

  return state;
}
