interface RiskBadgeProps {
  label: string;
}

export function RiskBadge({ label }: RiskBadgeProps) {
  return (
    <span className="inline-flex items-center gap-1.5 rounded-full border border-status-critical/30 bg-status-critical/10 px-2.5 py-1 text-xs font-medium text-status-critical">
      <svg viewBox="0 0 16 16" className="h-3 w-3 shrink-0" fill="none">
        <path
          d="M8 1.5 15 13.5H1L8 1.5Z"
          stroke="currentColor"
          strokeWidth="1.3"
          strokeLinejoin="round"
        />
        <path d="M8 6.5v3" stroke="currentColor" strokeWidth="1.3" strokeLinecap="round" />
        <circle cx="8" cy="11.2" r="0.6" fill="currentColor" />
      </svg>
      {label}
    </span>
  );
}
