import { useEffect, useRef, useState } from "react";
import { connectLiveFeed } from "@/services/ws";
import type { LiveAlert, LiveTransaction } from "@/types/api";

const MAX_TXNS = 60;
const MAX_ALERTS = 8;

export interface LiveFeedState {
  transactions: LiveTransaction[];
  alerts: LiveAlert[];
  connected: boolean;
  totalSeen: number;
  flaggedSeen: number;
}

/** Subscribes to the live WebSocket feed and keeps a bounded rolling buffer. */
export function useLiveFeed(): LiveFeedState {
  const [transactions, setTransactions] = useState<LiveTransaction[]>([]);
  const [alerts, setAlerts] = useState<LiveAlert[]>([]);
  const [connected, setConnected] = useState(false);
  const counts = useRef({ total: 0, flagged: 0 });
  const [, forceCount] = useState(0);

  useEffect(() => {
    const client = connectLiveFeed(
      (event) => {
        if (event.type === "transaction") {
          counts.current.total += 1;
          if (event.data.is_flagged) counts.current.flagged += 1;
          forceCount((n) => n + 1);
          setTransactions((prev) => [event.data, ...prev].slice(0, MAX_TXNS));
        } else {
          setAlerts((prev) => [event.data, ...prev].slice(0, MAX_ALERTS));
        }
      },
      setConnected,
    );
    return () => client.close();
  }, []);

  return {
    transactions,
    alerts,
    connected,
    totalSeen: counts.current.total,
    flaggedSeen: counts.current.flagged,
  };
}
