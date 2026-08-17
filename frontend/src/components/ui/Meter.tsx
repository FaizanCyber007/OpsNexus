interface MeterProps {
  label: string;
  value: number;
}

export function Meter({ label, value }: MeterProps) {
  const percent = Math.round(Math.max(0, Math.min(1, value)) * 100);

  return (
    <div className="flex flex-col gap-1">
      <div className="flex items-center justify-between text-xs text-white/50">
        <span>{label}</span>
        <span className="tabular-nums">{percent}%</span>
      </div>
      <div
        role="meter"
        aria-label={label}
        aria-valuenow={percent}
        aria-valuemin={0}
        aria-valuemax={100}
        className="h-1.5 w-full overflow-hidden rounded-full bg-white/10"
      >
        <div
          className="h-full rounded-full bg-gradient-to-r from-indigo-500 to-violet-500"
          style={{ width: `${percent}%` }}
        />
      </div>
    </div>
  );
}
