import type { Document } from "@/lib/types";

type BadgeStatus = Document["status"] | "error";

const STATUS_CONFIG: Record<
  BadgeStatus,
  { label: string; badgeClass: string; dotClass: string; icon: "dot-pulse" | "check" | "cross" }
> = {
  pending: {
    label: "Pending",
    badgeClass: "border-status-warning/30 bg-status-warning/10 text-status-warning",
    dotClass: "bg-status-warning",
    icon: "dot-pulse",
  },
  processing: {
    label: "Processing",
    badgeClass: "border-status-warning/30 bg-status-warning/10 text-status-warning",
    dotClass: "bg-status-warning",
    icon: "dot-pulse",
  },
  completed: {
    label: "Completed",
    badgeClass: "border-status-good/30 bg-status-good/10 text-status-good",
    dotClass: "bg-status-good",
    icon: "check",
  },
  failed: {
    label: "Failed",
    badgeClass: "border-status-critical/30 bg-status-critical/10 text-status-critical",
    dotClass: "bg-status-critical",
    icon: "cross",
  },
  error: {
    label: "Error",
    badgeClass: "border-status-critical/30 bg-status-critical/10 text-status-critical",
    dotClass: "bg-status-critical",
    icon: "cross",
  },
};

interface StatusBadgeProps {
  status: BadgeStatus;
}

export function StatusBadge({ status }: StatusBadgeProps) {
  const { label, badgeClass, dotClass, icon } = STATUS_CONFIG[status];

  return (
    <span
      className={`inline-flex items-center gap-1.5 rounded-full border px-2.5 py-1 text-xs font-medium ${badgeClass}`}
    >
      {icon === "dot-pulse" && (
        <span className={`h-1.5 w-1.5 animate-pulse rounded-full ${dotClass}`} />
      )}
      {icon === "check" && (
        <svg viewBox="0 0 16 16" className="h-3 w-3" fill="none">
          <path
            d="M3.5 8.5 6.5 11.5 12.5 4.5"
            stroke="currentColor"
            strokeWidth="1.75"
            strokeLinecap="round"
            strokeLinejoin="round"
          />
        </svg>
      )}
      {icon === "cross" && (
        <svg viewBox="0 0 16 16" className="h-3 w-3" fill="none">
          <path
            d="M4 4 12 12M12 4 4 12"
            stroke="currentColor"
            strokeWidth="1.75"
            strokeLinecap="round"
          />
        </svg>
      )}
      {label}
    </span>
  );
}
