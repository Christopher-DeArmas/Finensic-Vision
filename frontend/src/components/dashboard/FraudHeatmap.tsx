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
import type { DashboardStats } from "@/types/api";

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

export function FraudHeatmap({ stats }: { stats: DashboardStats }) {
  const [pos, setPos] = useState<Position>(INITIAL);
  const k = pos.zoom; // divisor keeps markers a constant screen size while zooming

  const flagged = stats.heatmap.filter((p) => p.is_flagged);
  const normal = stats.heatmap.filter((p) => !p.is_flagged);

  const setZoom = (z: number) =>
    setPos((p) => ({ ...p, zoom: Math.min(MAX_ZOOM, Math.max(MIN_ZOOM, z)) }));

  const btn =
    "grid h-7 w-7 place-items-center rounded-md border border-white/10 bg-ink-900/80 text-white/70 backdrop-blur transition-colors hover:border-gold-500/40 hover:text-gold-300";

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
        <div className="h-[320px] w-full overflow-hidden">
          <ComposableMap
            projection="geoEqualEarth"
            projectionConfig={{ scale: 165 }}
            width={800}
            height={360}
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
                  <circle r={1.5 / k} fill="#d4af37" fillOpacity={0.55} />
                </Marker>
              ))}
              {flagged.map((p, i) => (
                <Marker key={`f${i}`} coordinates={[p.longitude, p.latitude]}>
                  <circle r={2.4 / k} fill="#ef4444" fillOpacity={0.9} />
                  <circle
                    r={4.2 / k}
                    fill="none"
                    stroke="#ef4444"
                    strokeOpacity={0.35}
                    strokeWidth={0.8 / k}
                  />
                </Marker>
              ))}
            </ZoomableGroup>
          </ComposableMap>
        </div>

        {/* Zoom controls */}
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
          Drag to pan · scroll or use +/− to zoom · red marks rule-flagged
          activity.
        </p>
      </div>
    </Panel>
  );
}
