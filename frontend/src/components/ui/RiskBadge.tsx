import { AlertTriangle, AlertCircle, ShieldAlert } from "lucide-react";
import { cn } from "@/lib/utils";

interface RiskBadgeProps {
  label: string;
  severity?: "critical" | "high" | "medium" | "low";
  className?: string;
}

const SEVERITY_CONFIG = {
  critical: "border-rose-500/30 bg-rose-500/10 text-rose-300",
  high: "border-orange-500/30 bg-orange-500/10 text-orange-300",
  medium: "border-amber-500/30 bg-amber-500/10 text-amber-300",
  low: "border-blue-500/30 bg-blue-500/10 text-blue-300",
};

export function RiskBadge({ label, severity = "low", className = "" }: RiskBadgeProps) {
  const resolvedSeverity = severity || "low";

  const Icon =
    resolvedSeverity === "critical"
      ? ShieldAlert
      : resolvedSeverity === "high"
      ? AlertTriangle
      : AlertCircle;

  return (
    <span
      className={cn(
        "inline-flex items-center gap-1.5 rounded-full border px-2.5 py-1 text-xs font-medium backdrop-blur-md transition-colors select-none",
        SEVERITY_CONFIG[resolvedSeverity],
        className
      )}
    >
      <Icon className="h-3 w-3 shrink-0" />
      <span>{label}</span>
    </span>
  );
}
