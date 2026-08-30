import { CheckCircle2, Clock, Loader2, XCircle, AlertCircle } from "lucide-react";
import type { Document } from "@/lib/types";
import { cn } from "@/lib/utils";

export type BadgeStatus =
  | Document["status"]
  | "running"
  | "succeeded"
  | "error";

interface StatusConfig {
  label: string;
  badgeClass: string;
  dotClass: string;
  icon: typeof CheckCircle2;
  animateIcon?: boolean;
}

const STATUS_CONFIG: Record<BadgeStatus, StatusConfig> = {
  pending: {
    label: "Pending",
    badgeClass: "border-amber-500/25 bg-amber-500/10 text-amber-300",
    dotClass: "bg-amber-400",
    icon: Clock,
  },
  processing: {
    label: "Processing",
    badgeClass: "border-indigo-500/30 bg-indigo-500/10 text-indigo-300 shadow-sm shadow-indigo-500/10",
    dotClass: "bg-indigo-400",
    icon: Loader2,
    animateIcon: true,
  },
  running: {
    label: "Running",
    badgeClass: "border-indigo-500/30 bg-indigo-500/10 text-indigo-300 shadow-sm shadow-indigo-500/10",
    dotClass: "bg-indigo-400",
    icon: Loader2,
    animateIcon: true,
  },
  completed: {
    label: "Completed",
    badgeClass: "border-emerald-500/25 bg-emerald-500/10 text-emerald-300",
    dotClass: "bg-emerald-400",
    icon: CheckCircle2,
  },
  succeeded: {
    label: "Succeeded",
    badgeClass: "border-emerald-500/25 bg-emerald-500/10 text-emerald-300",
    dotClass: "bg-emerald-400",
    icon: CheckCircle2,
  },
  failed: {
    label: "Failed",
    badgeClass: "border-rose-500/25 bg-rose-500/10 text-rose-300",
    dotClass: "bg-rose-400",
    icon: XCircle,
  },
  error: {
    label: "Error",
    badgeClass: "border-rose-500/25 bg-rose-500/10 text-rose-300",
    dotClass: "bg-rose-400",
    icon: AlertCircle,
  },
};

interface StatusBadgeProps {
  status: BadgeStatus;
  size?: "sm" | "md";
  className?: string;
  showIcon?: boolean;
}

export function StatusBadge({
  status,
  size = "md",
  className = "",
  showIcon = true,
}: StatusBadgeProps) {
  const config = STATUS_CONFIG[status] || STATUS_CONFIG.pending;
  const Icon = config.icon;

  return (
    <span
      className={cn(
        "inline-flex items-center gap-1.5 font-medium rounded-full border backdrop-blur-md transition-all select-none",
        size === "sm" ? "px-2 py-0.5 text-[11px]" : "px-2.5 py-1 text-xs",
        config.badgeClass,
        className
      )}
    >
      {showIcon && (
        <Icon
          className={cn(
            size === "sm" ? "h-3 w-3" : "h-3.5 w-3.5",
            config.animateIcon && "animate-spin"
          )}
        />
      )}
      {config.label}
    </span>
  );
}
