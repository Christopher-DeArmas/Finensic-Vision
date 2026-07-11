import {
  createContext,
  useContext,
  useEffect,
  useRef,
  useState,
  type ReactNode,
} from "react";
import { connectLiveFeed } from "@/services/ws";
import type { LiveTransaction } from "@/types/api";

export interface HeatPt {
  id: string;
  latitude: number;
  longitude: number;
  amount: number;
  country: string;
  city: string;
  type: string;
  is_flagged: boolean;
  label: string | null;
}

interface LiveData {
  transactions: LiveTransaction[];
  heatPoints: HeatPt[];
  connected: boolean;
  totalSeen: number;
  flaggedSeen: number;
}

const Ctx = createContext<LiveData>({
  transactions: [],
  heatPoints: [],
  connected: false,
  totalSeen: 0,
  flaggedSeen: 0,
});

export const useLiveData = () => useContext(Ctx);

const MAX_FEED = 60;
const MAX_HEAT = 400;

/**
 * Holds the single WebSocket connection and the accumulated live data. Mounted
 * once in the app shell so the feed, heatmap and counters persist across route
 * changes instead of resetting every time the user switches tabs (item 3).
 */
export function LiveDataProvider({ children }: { children: ReactNode }) {
  const [transactions, setTransactions] = useState<LiveTransaction[]>([]);
  const [heatPoints, setHeatPoints] = useState<HeatPt[]>([]);
  const [connected, setConnected] = useState(false);
  const counts = useRef({ total: 0, flagged: 0 });
  const [, force] = useState(0);

  useEffect(() => {
    const client = connectLiveFeed((ev) => {
      if (ev.type !== "transaction") return;
      const t = ev.data;
      counts.current.total += 1;
      if (t.is_flagged) counts.current.flagged += 1;
      force((n) => n + 1);
      setTransactions((prev) => [t, ...prev].slice(0, MAX_FEED));
      setHeatPoints((prev) =>
        [
          {
            id: t.external_id,
            latitude: t.latitude,
            longitude: t.longitude,
            amount: t.amount,
            country: t.country,
            city: t.city,
            type: t.transaction_type,
            is_flagged: t.is_flagged,
            label: t.merchant_name || t.sender_name || t.receiver_name || null,
          },
          ...prev,
        ].slice(0, MAX_HEAT),
      );
    }, setConnected);
    return () => client.close();
  }, []);

  return (
    <Ctx.Provider
      value={{
        transactions,
        heatPoints,
        connected,
        totalSeen: counts.current.total,
        flaggedSeen: counts.current.flagged,
      }}
    >
      {children}
    </Ctx.Provider>
  );
}
