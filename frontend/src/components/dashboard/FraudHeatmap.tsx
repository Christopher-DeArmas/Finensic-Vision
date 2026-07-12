import { useRef, useState } from "react";
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
import { formatCurrency } from "@/lib/format";
import { useLiveData, type HeatPt } from "@/contexts/LiveDataProvider";

const geography = worldTopo as object;
const MIN_ZOOM = 1;
const MAX_ZOOM = 8;
const INITIAL: { coordinates: [number, number]; zoom: number } = {
  coordinates: [5, 20],
  zoom: 1,
};

interface Position {
  coordinates: [number, number];
  zoom: number;
}
type Pt = HeatPt;
interface Hover {
  p: Pt;
  x: number;
  y: number;
}

export function FraudHeatmap() {
  const { heatPoints } = useLiveData();
  const [pos, setPos] = useState<Position>(INITIAL);
  const [hover, setHover] = useState<Hover | null>(null);
  const wrapRef = useRef<HTMLDivElement>(null);
  const k = pos.zoom;

  const points = heatPoints;
  const flagged = points.filter((p) => p.is_flagged);
  const normal = points.filter((p) => !p.is_flagged);

  const setZoom = (z: number) =>
    setPos((p) => ({ ...p, zoom: Math.min(MAX_ZOOM, Math.max(MIN_ZOOM, z)) }));

  const onEnter = (e: React.MouseEvent, p: Pt) => {
    const rect = wrapRef.current?.getBoundingClientRect();
    if (!rect) return;
    setHover({ p, x: e.clientX - rect.left, y: e.clientY - rect.top });
  };

  const btn =
    "grid h-7 w-7 place-items-center rounded-md border border-white/10 bg-ink-900/80 text-white/70 backdrop-blur transition-colors hover:border-gold-500/40 hover:text-gold-300";

  return (
    <Panel title="Fraud Heatmap" icon={<Globe2 size={16} />} bodyClassName="p-0">
      <div ref={wrapRef} className="relative">
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
              // Block wheel / trackpad / double-click zoom; drag-pan still works (item 12).
              filterZoomEvent={((e: Event) =>
                e.type !== "wheel" && e.type !== "dblclick") as never}
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

              {normal.map((p) => (
                <Marker key={p.id} coordinates={[p.longitude, p.latitude]}>
                  <circle
                    r={1.6 / k}
                    fill="#d4af37"
                    fillOpacity={0.55}
                    className="cursor-pointer"
                    onMouseEnter={(e) => onEnter(e, p)}
                    onMouseLeave={() => setHover(null)}
                  />
                </Marker>
              ))}
              {flagged.map((p) => (
                <Marker key={p.id} coordinates={[p.longitude, p.latitude]}>
                  <circle r={4.4 / k} fill="none" stroke="#ef4444" strokeOpacity={0.35} strokeWidth={0.8 / k} />
                  <circle
                    r={2.6 / k}
                    fill="#ef4444"
                    fillOpacity={0.9}
                    className="cursor-pointer"
                    onMouseEnter={(e) => onEnter(e, p)}
                    onMouseLeave={() => setHover(null)}
                  />
                </Marker>
              ))}
            </ZoomableGroup>
          </ComposableMap>
        </div>

        {/* Hover popup with transaction details (item 4) */}
        {hover && (
          <div
            className="pointer-events-none absolute z-20 w-52 -translate-x-1/2 -translate-y-full rounded-lg border border-white/10 bg-ink-900/95 p-2.5 shadow-card backdrop-blur"
            style={{ left: hover.x, top: hover.y - 8 }}
          >
            <div className="flex items-center justify-between gap-2">
              <span className="truncate text-xs font-semibold text-white/90">
                {hover.p.label ?? "Unknown"}
              </span>
              {hover.p.is_flagged && (
                <span className="text-[10px] font-bold uppercase text-risk-critical">
                  Flagged
                </span>
              )}
            </div>
            <div className="mt-1 text-[11px] text-white/50">
              {hover.p.type} · {hover.p.city}, {hover.p.country}
            </div>
            <div
              className="mt-0.5 text-sm font-bold tabular-nums"
              style={{ color: hover.p.is_flagged ? "#ef4444" : "#d4af37" }}
            >
              {formatCurrency(hover.p.amount)}
            </div>
          </div>
        )}

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
          Live transactions plotted as they stream · drag to pan · hover a point
          for details · red marks rule-flagged activity.
        </p>
      </div>
    </Panel>
  );
}
