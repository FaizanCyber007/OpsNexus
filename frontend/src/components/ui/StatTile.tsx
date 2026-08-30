import type { ReactNode } from "react";
import { cn } from "@/lib/utils";

interface StatTileProps {
  label: string;
  value: number | string;
  icon?: ReactNode;
  accentClass?: string;
  subtext?: string;
  className?: string;
}

export function StatTile({
  label,
  value,
  icon,
  accentClass = "text-white",
  subtext,
  className = "",
}: StatTileProps) {
  return (
    <div
      className={cn(
        "group relative flex-1 overflow-hidden rounded-2xl border border-white/[0.08] bg-[#111116]/80 p-4 backdrop-blur-xl transition-all duration-200 hover:border-white/[0.15] hover:bg-[#14141a]",
        className
      )}
    >
      <div className="flex items-center justify-between">
        <p className="text-[11px] font-semibold uppercase tracking-wider text-white/40">
          {label}
        </p>
        {icon && (
          <div className="flex h-7 w-7 items-center justify-center rounded-lg bg-white/[0.04] text-white/50 group-hover:text-white/80 group-hover:bg-white/[0.08] transition-colors">
            {icon}
          </div>
        )}
      </div>

      <div className="mt-2 flex items-baseline gap-2">
        <p className={cn("text-2xl font-bold tracking-tight tabular-nums", accentClass)}>
          {value}
        </p>
        {subtext && <span className="text-[11px] text-white/40">{subtext}</span>}
      </div>
    </div>
  );
}
