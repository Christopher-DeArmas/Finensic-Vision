import type { WsEvent } from "@/types/api";

function defaultWsUrl(): string {
  if (import.meta.env.VITE_WS_URL) return import.meta.env.VITE_WS_URL;
  const proto = window.location.protocol === "https:" ? "wss" : "ws";
  return `${proto}://${window.location.host}/ws/transactions`;
}

export interface WsClient {
  close: () => void;
}

/**
 * Connects to the live transaction stream and invokes `onEvent` for every
 * message. Automatically reconnects with backoff until `close()` is called.
 */
export function connectLiveFeed(
  onEvent: (event: WsEvent) => void,
  onStatus?: (connected: boolean) => void,
): WsClient {
  const url = defaultWsUrl();
  let socket: WebSocket | null = null;
  let stopped = false;
  let retry = 0;
  let timer: ReturnType<typeof setTimeout> | undefined;

  const open = () => {
    if (stopped) return;
    socket = new WebSocket(url);

    socket.onopen = () => {
      retry = 0;
      onStatus?.(true);
    };
    socket.onmessage = (ev) => {
      try {
        onEvent(JSON.parse(ev.data) as WsEvent);
      } catch {
        /* ignore malformed frames */
      }
    };
    socket.onclose = () => {
      onStatus?.(false);
      if (stopped) return;
      retry += 1;
      const delay = Math.min(1000 * 2 ** retry, 10_000);
      timer = setTimeout(open, delay);
    };
    socket.onerror = () => socket?.close();
  };

  open();

  return {
    close: () => {
      stopped = true;
      if (timer) clearTimeout(timer);
      socket?.close();
    },
  };
}
