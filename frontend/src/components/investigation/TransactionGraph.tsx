import { useMemo } from "react";
import ReactFlow, {
  Background,
  BackgroundVariant,
  Controls,
  Handle,
  MarkerType,
  Position,
  type Edge,
  type Node,
  type NodeProps,
} from "reactflow";
import "reactflow/dist/style.css";
import { Building2, User } from "lucide-react";
import { RISK_COLORS } from "@/components/ui/RiskBadge";
import { formatCurrency } from "@/lib/format";
import type { GraphData, RiskLevel } from "@/types/api";

interface NodeData {
  label: string;
  sublabel: string | null;
  kind: "customer" | "merchant";
  risk_level: RiskLevel | null;
  is_subject: boolean;
  is_high_risk: boolean;
  amount: number;
}

function FvNode({ data }: NodeProps<NodeData>) {
  const color = data.risk_level ? RISK_COLORS[data.risk_level] : "#8a8a92";
  const accent = data.is_high_risk ? "#ef4444" : color;

  return (
    <div
      className="flex items-center gap-2 rounded-xl border bg-ink-850/95 px-3 py-2 shadow-card"
      style={{
        borderColor: data.is_subject ? "#d4af37" : `${accent}55`,
        boxShadow: data.is_subject
          ? "0 0 0 2px rgba(212,175,55,0.35)"
          : undefined,
        minWidth: 120,
        maxWidth: 190,
      }}
    >
      <Handle type="target" position={Position.Left} style={{ opacity: 0 }} />
      <span
        className="grid h-7 w-7 shrink-0 place-items-center rounded-lg"
        style={{ backgroundColor: `${accent}22`, color: accent }}
      >
        {data.kind === "merchant" ? <Building2 size={14} /> : <User size={14} />}
      </span>
      <div className="min-w-0">
        <div className="truncate text-xs font-semibold text-white/90">
          {data.label}
        </div>
        <div className="truncate text-[10px] text-white/40">
          {data.is_subject
            ? "Subject"
            : data.kind === "merchant"
              ? data.is_high_risk
                ? "High-risk merchant"
                : "Merchant"
              : `${formatCurrency(data.amount)}`}
        </div>
      </div>
      <Handle type="source" position={Position.Right} style={{ opacity: 0 }} />
    </div>
  );
}

const nodeTypes = { fv: FvNode };

export function TransactionGraph({ graph }: { graph: GraphData }) {
  const { nodes, edges } = useMemo(() => {
    const others = graph.nodes.filter((n) => !n.is_subject);
    const radius = Math.max(260, 90 + others.length * 12);
    const cx = 0;
    const cy = 0;

    const rfNodes: Node<NodeData>[] = graph.nodes.map((n) => {
      let x = cx;
      let y = cy;
      if (!n.is_subject) {
        const i = others.findIndex((o) => o.id === n.id);
        const angle = (2 * Math.PI * i) / others.length - Math.PI / 2;
        x = cx + radius * Math.cos(angle);
        y = cy + radius * Math.sin(angle);
      }
      return {
        id: n.id,
        type: "fv",
        position: { x, y },
        data: {
          label: n.label,
          sublabel: n.sublabel,
          kind: n.kind,
          risk_level: n.risk_level,
          is_subject: n.is_subject,
          is_high_risk: n.is_high_risk,
          amount: n.total_amount,
        },
      };
    });

    const rfEdges: Edge[] = graph.edges.map((e) => ({
      id: e.id,
      source: e.source,
      target: e.target,
      animated: e.suspicious,
      label: e.suspicious ? formatCurrency(e.amount) : undefined,
      labelStyle: { fill: "#ef4444", fontSize: 10 },
      labelBgStyle: { fill: "#0c0c0f", fillOpacity: 0.8 },
      style: {
        stroke: e.suspicious ? "#ef4444" : "rgba(212,175,55,0.35)",
        strokeWidth: e.suspicious ? 2 : 1.4,
      },
      markerEnd: {
        type: MarkerType.ArrowClosed,
        color: e.suspicious ? "#ef4444" : "rgba(212,175,55,0.5)",
        width: 16,
        height: 16,
      },
    }));

    return { nodes: rfNodes, edges: rfEdges };
  }, [graph]);

  return (
    <ReactFlow
      nodes={nodes}
      edges={edges}
      nodeTypes={nodeTypes}
      fitView
      fitViewOptions={{ padding: 0.2 }}
      minZoom={0.2}
      maxZoom={2.5}
      proOptions={{ hideAttribution: true }}
      className="rounded-b-2xl"
    >
      <Background variant={BackgroundVariant.Dots} gap={22} size={1} color="#26262c" />
      <Controls
        showInteractive={false}
        className="!border-white/10 !bg-ink-900/80 [&_button]:!border-white/10 [&_button]:!bg-ink-850 [&_button]:!fill-white/70"
      />
    </ReactFlow>
  );
}
