import { useState } from "react";
import {
  ComposableMap,
  Geographies,
  Geography,
  Marker,
  ZoomableGroup,
} from "react-simple-maps";
import { Globe2, Minus, Plus, RotateCcw } from "lucide-react";
import worldTopo from "world-atlas/countries-110m.json";
import { Panel } from "@/components/ui/Card";
import { Badge } from "@/components/ui/Badge";
import { formatCurrency } from "@/lib/format";
import type { DashboardStats, LiveTransaction } from "@/types/api";

const geography = worldTopo as object;
const MIN_ZOOM = 1;
const MAX_ZOOM = 8;
const INITIAL: { coordinates: [number, number]; zoom: number } = {
  coordinates: [5, 20],
  zoom: 1,
};
const MAX_POINTS = 600;

interface Position {
  coordinates: [number, number];
  zoom: number;
}
interface Pt {
  latitude: number;
  longitude: number;
  amount: number;
  country: string;
  is_flagged: boolean;
  label?: string | null;
}

export function FraudHeatmap({
  stats,
  livePoints = [],
}: {
  stats: DashboardStats;
  livePoints?: LiveTransaction[];
}) {
  const [pos, setPos] = useState<Position>(INITIAL);
  const k = pos.zoom;

  // Live transactions stream in front of the seeded snapshot, so the map and
  // its counts update continuously (items 9 & 12).
  const live: Pt[] = livePoints.map((t) => ({
    latitude: t.latitude,
    longitude: t.longitude,
    amount: t.amount,
    country: t.country,
    is_flagged: t.is_flagged,
    label: t.merchant_name || t.sender_name || t.receiver_name || null,
  }));
  const all: Pt[] = [...live, ...stats.heatmap].slice(0, MAX_POINTS);
  const flagged = all.filter((p) => p.is_flagged);
  const normal = all.filter((p) => !p.is_flagged);

  const setZoom = (z: number) =>
    setPos((p) => ({ ...p, zoom: Math.min(MAX_ZOOM, Math.max(MIN_ZOOM, z)) }));

  const btn =
    "grid h-7 w-7 place-items-center rounded-md border border-white/10 bg-ink-900/80 text-white/70 backdrop-blur transition-colors hover:border-gold-500/40 hover:text-gold-300";

  const title = (p: Pt) =>
    `${p.label ?? "Unknown"} · ${formatCurrency(p.amount)} · ${p.country}${
      p.is_flagged ? " · FLAGGED" : ""
    }`;

  return (
    <Panel
      title="Fraud Heatmap"
      icon={<Globe2 size={16} />}
      bodyClassName="p-0"
      action={
        <div className="flex items-center gap-2">
          <Badge className="border-gold-500/25 bg-gold-500/10 text-gold-300">
            {normal.length} normal
          </Badge>
          <Badge className="border-risk-critical/30 bg-risk-critical/10 text-risk-critical">
            {flagged.length} flagged
          </Badge>
        </div>
      }
    >
      <div className="relative">
        <div className="h-[360px] w-full overflow-hidden">
          <ComposableMap
            projection="geoEqualEarth"
            projectionConfig={{ scale: 165 }}
            width={800}
            height={400}
            style={{ width: "100%", height: "100%" }}
          >
            <ZoomableGroup
              center={pos.coordinates}
              zoom={pos.zoom}
              minZoom={MIN_ZOOM}
              maxZoom={MAX_ZOOM}
              onMoveEnd={(p) => setPos(p as Position)}
            >
              <Geographies geography={geography}>
                {({ geographies }) =>
                  geographies.map((geo) => (
                    <Geography
                      key={geo.rsmKey}
                      geography={geo}
                      fill="#17171c"
                      stroke="#2c2c34"
                      strokeWidth={0.4 / k}
                      style={{
                        default: { outline: "none" },
                        hover: { fill: "#1e1e25", outline: "none" },
                        pressed: { outline: "none" },
                      }}
                    />
                  ))
                }
              </Geographies>

              {normal.map((p, i) => (
                <Marker key={`n${i}`} coordinates={[p.longitude, p.latitude]}>
                  <circle r={1.5 / k} fill="#d4af37" fillOpacity={0.55}>
                    <title>{title(p)}</title>
                  </circle>
                </Marker>
              ))}
              {flagged.map((p, i) => (
                <Marker key={`f${i}`} coordinates={[p.longitude, p.latitude]}>
                  <circle r={4.2 / k} fill="none" stroke="#ef4444" strokeOpacity={0.35} strokeWidth={0.8 / k} />
                  <circle r={2.4 / k} fill="#ef4444" fillOpacity={0.9} className="cursor-pointer">
                    <title>{title(p)}</title>
                  </circle>
                </Marker>
              ))}
            </ZoomableGroup>
          </ComposableMap>
        </div>

        <div className="absolute right-3 top-3 flex flex-col gap-1">
          <button className={btn} onClick={() => setZoom(k * 1.6)} aria-label="Zoom in">
            <Plus size={14} />
          </button>
          <button className={btn} onClick={() => setZoom(k / 1.6)} aria-label="Zoom out">
            <Minus size={14} />
          </button>
          <button className={btn} onClick={() => setPos(INITIAL)} aria-label="Reset view">
            <RotateCcw size={13} />
          </button>
        </div>

        <p className="px-4 py-2 text-[11px] text-white/35">
          Drag to pan · scroll or +/− to zoom · hover a point for details · red
          marks rule-flagged activity.
        </p>
      </div>
    </Panel>
  );
}
