import { useMemo, useRef, useState } from "react";
import { Minus, Plus, RotateCcw } from "lucide-react";
import { RISK_COLORS } from "@/components/ui/RiskBadge";
import { formatCurrency } from "@/lib/format";
import type { GraphData, RiskLevel } from "@/types/api";

interface Pt {
  x: number;
  y: number;
}

/**
 * Self-contained SVG transaction-network graph: subject at centre, counterparties
 * and merchants around it. Drag to pan, scroll / buttons to zoom. No external
 * graph engine, so it always renders.
 */
export function TransactionGraph({ graph }: { graph: GraphData }) {
  const [view, setView] = useState({ k: 1, tx: 0, ty: 0 });
  const drag = useRef<{ x: number; y: number; tx: number; ty: number } | null>(null);

  const { positions, radius } = useMemo(() => {
    const others = graph.nodes.filter((n) => !n.is_subject);
    const R = Math.max(190, 70 + others.length * 11);
    const pos: Record<string, Pt> = {};
    graph.nodes.forEach((n) => {
      if (n.is_subject) {
        pos[n.id] = { x: 0, y: 0 };
      } else {
        const i = others.findIndex((o) => o.id === n.id);
        const a = (2 * Math.PI * i) / Math.max(others.length, 1) - Math.PI / 2;
        pos[n.id] = { x: Math.cos(a) * R, y: Math.sin(a) * R };
      }
    });
    return { positions: pos, radius: R };
  }, [graph]);

  const pad = 150;
  const vb = radius + pad;

  const setZoom = (k: number) =>
    setView((v) => ({ ...v, k: Math.min(3, Math.max(0.4, k)) }));

  const onWheel = (e: React.WheelEvent) => {
    e.preventDefault();
    setZoom(view.k * (e.deltaY < 0 ? 1.12 : 0.89));
  };
  const onDown = (e: React.MouseEvent) => {
    drag.current = { x: e.clientX, y: e.clientY, tx: view.tx, ty: view.ty };
  };
  const onMove = (e: React.MouseEvent) => {
    if (!drag.current) return;
    setView((v) => ({
      ...v,
      tx: drag.current!.tx + (e.clientX - drag.current!.x),
      ty: drag.current!.ty + (e.clientY - drag.current!.y),
    }));
  };
  const onUp = () => (drag.current = null);

  const btn =
    "grid h-7 w-7 place-items-center rounded-md border border-white/10 bg-ink-900/80 text-white/70 backdrop-blur transition-colors hover:border-gold-500/40 hover:text-gold-300";

  return (
    <div className="relative h-full w-full overflow-hidden">
      <svg
        className="h-full w-full cursor-grab active:cursor-grabbing"
        viewBox={`${-vb} ${-vb} ${2 * vb} ${2 * vb}`}
        preserveAspectRatio="xMidYMid meet"
        onWheel={onWheel}
        onMouseDown={onDown}
        onMouseMove={onMove}
        onMouseUp={onUp}
        onMouseLeave={onUp}
      >
        <defs>
          <marker id="arrow-gold" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
            <path d="M0 0 L10 5 L0 10 z" fill="rgba(212,175,55,0.55)" />
          </marker>
          <marker id="arrow-red" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
            <path d="M0 0 L10 5 L0 10 z" fill="#ef4444" />
          </marker>
        </defs>

        <g transform={`translate(${view.tx} ${view.ty}) scale(${view.k})`}>
          {/* Edges */}
          {graph.edges.map((e) => {
            const s = positions[e.source];
            const t = positions[e.target];
            if (!s || !t) return null;
            const mx = (s.x + t.x) / 2;
            const my = (s.y + t.y) / 2;
            return (
              <g key={e.id}>
                <line
                  x1={s.x}
                  y1={s.y}
                  x2={t.x}
                  y2={t.y}
                  stroke={e.suspicious ? "#ef4444" : "rgba(212,175,55,0.32)"}
                  strokeWidth={e.suspicious ? 2 : 1.2}
                  markerEnd={`url(#${e.suspicious ? "arrow-red" : "arrow-gold"})`}
                  strokeDasharray={e.suspicious ? "6 4" : undefined}
                >
                  {e.suspicious && (
                    <animate
                      attributeName="stroke-dashoffset"
                      from="20"
                      to="0"
                      dur="0.8s"
                      repeatCount="indefinite"
                    />
                  )}
                </line>
                {e.suspicious && (
                  <text x={mx} y={my - 3} fill="#ef4444" fontSize={11} textAnchor="middle">
                    {formatCurrency(e.amount)}
                  </text>
                )}
              </g>
            );
          })}

          {/* Nodes */}
          {graph.nodes.map((n) => {
            const p = positions[n.id];
            if (!p) return null;
            const color = n.is_high_risk
              ? "#ef4444"
              : n.risk_level
                ? RISK_COLORS[n.risk_level as RiskLevel]
                : "#8a8a92";
            const r = n.is_subject ? 26 : 18;
            const label =
              n.label.length > 18 ? `${n.label.slice(0, 17)}…` : n.label;
            return (
              <g key={n.id} transform={`translate(${p.x} ${p.y})`}>
                {n.is_subject && (
                  <circle r={r + 6} fill="none" stroke="#d4af37" strokeWidth={2} opacity={0.6} />
                )}
                {n.kind === "merchant" ? (
                  <rect
                    x={-r}
                    y={-r}
                    width={r * 2}
                    height={r * 2}
                    rx={6}
                    fill={`${color}22`}
                    stroke={color}
                    strokeWidth={1.5}
                  />
                ) : (
                  <circle
                    r={r}
                    fill={`${color}22`}
                    stroke={color}
                    strokeWidth={n.is_subject ? 2.4 : 1.6}
                  />
                )}
                <text
                  y={r + 15}
                  fill="rgba(255,255,255,0.85)"
                  fontSize={n.is_subject ? 14 : 12}
                  fontWeight={n.is_subject ? 700 : 500}
                  textAnchor="middle"
                >
                  {label}
                </text>
              </g>
            );
          })}
        </g>
      </svg>

      <div className="absolute right-3 top-3 flex flex-col gap-1">
        <button className={btn} onClick={() => setZoom(view.k * 1.3)} aria-label="Zoom in">
          <Plus size={14} />
        </button>
        <button className={btn} onClick={() => setZoom(view.k / 1.3)} aria-label="Zoom out">
          <Minus size={14} />
        </button>
        <button className={btn} onClick={() => setView({ k: 1, tx: 0, ty: 0 })} aria-label="Reset">
          <RotateCcw size={13} />
        </button>
      </div>

      <div className="pointer-events-none absolute bottom-3 left-4 flex items-center gap-3 text-[11px] text-white/40">
        <span className="flex items-center gap-1.5">
          <span className="inline-block h-2 w-2 rounded-full" style={{ background: "#ef4444" }} />
          suspicious
        </span>
        <span>drag to pan · scroll to zoom</span>
      </div>
    </div>
  );
}
