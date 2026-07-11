import { useCallback, useEffect, useState } from "react";
import { api } from "@/services/api";
import type { InvestigationBundle } from "@/types/api";

interface State {
  bundle: InvestigationBundle | null;
  loading: boolean;
  error: string | null;
}

export function useInvestigation(customerId: number) {
  const [state, setState] = useState<State>({
    bundle: null,
    loading: true,
    error: null,
  });

  const load = useCallback(async () => {
    setState((s) => ({ ...s, loading: true }));
    try {
      const bundle = await api.investigation(customerId);
      setState({ bundle, loading: false, error: null });
    } catch (err) {
      setState({
        bundle: null,
        loading: false,
        error: err instanceof Error ? err.message : "Failed to load",
      });
    }
  }, [customerId]);

  useEffect(() => {
    void load();
  }, [load]);

  return { ...state, reload: load };
}
