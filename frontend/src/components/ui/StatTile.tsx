interface StatTileProps {
  label: string;
  value: number;
  accentClass?: string;
}

export function StatTile({ label, value, accentClass = "text-white" }: StatTileProps) {
  return (
    <div className="flex-1 rounded-xl border border-white/10 bg-white/5 px-4 py-3 backdrop-blur-xl">
      <p className="text-xs font-medium uppercase tracking-wide text-white/50">{label}</p>
      <p className={`mt-1 text-2xl font-semibold tabular-nums ${accentClass}`}>{value}</p>
    </div>
  );
}
