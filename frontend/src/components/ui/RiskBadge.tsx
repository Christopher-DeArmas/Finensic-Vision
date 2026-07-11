import { Badge } from "@/components/ui/Badge";
import { cn } from "@/lib/cn";
import type { RiskLevel, Severity } from "@/types/api";

const STYLES: Record<RiskLevel, string> = {
  low: "border-risk-low/25 bg-risk-low/10 text-risk-low",
  medium: "border-risk-medium/25 bg-risk-medium/10 text-risk-medium",
  high: "border-risk-high/25 bg-risk-high/10 text-risk-high",
  critical: "border-risk-critical/30 bg-risk-critical/10 text-risk-critical",
};

export function RiskBadge({
  level,
  className,
}: {
  level: RiskLevel | Severity;
  className?: string;
}) {
  return (
    <Badge className={cn(STYLES[level as RiskLevel], "capitalize", className)}>
      {level}
    </Badge>
  );
}

export const RISK_COLORS: Record<RiskLevel, string> = {
  low: "#34d399",
  medium: "#eab308",
  high: "#f97316",
  critical: "#ef4444",
};
