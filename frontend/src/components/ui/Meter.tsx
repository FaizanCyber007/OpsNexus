"use client";

import { motion } from "framer-motion";
import { cn } from "@/lib/utils";

interface MeterProps {
  label: string;
  value: number; // 0 to 1
  className?: string;
  showPercent?: boolean;
}

export function Meter({ label, value, className = "", showPercent = true }: MeterProps) {
  const percent = Math.round(Math.max(0, Math.min(1, value)) * 100);

  const getGradientClass = (pct: number) => {
    if (pct >= 80) return "from-emerald-500 to-teal-400";
    if (pct >= 50) return "from-amber-500 to-yellow-400";
    return "from-rose-500 to-orange-400";
  };

  const getTextColorClass = (pct: number) => {
    if (pct >= 80) return "text-emerald-400";
    if (pct >= 50) return "text-amber-400";
    return "text-rose-400";
  };

  return (
    <div className={cn("flex flex-col gap-1.5", className)}>
      <div className="flex items-center justify-between text-xs text-white/60">
        <span className="font-medium">{label}</span>
        {showPercent && (
          <span className={cn("font-mono font-semibold tabular-nums", getTextColorClass(percent))}>
            {percent}%
          </span>
        )}
      </div>
      <div
        role="meter"
        aria-label={label}
        aria-valuenow={percent}
        aria-valuemin={0}
        aria-valuemax={100}
        className="h-2 w-full overflow-hidden rounded-full bg-white/[0.08] p-0.5 border border-white/[0.05]"
      >
        <motion.div
          initial={{ width: 0 }}
          animate={{ width: `${percent}%` }}
          transition={{ duration: 0.8, ease: "easeOut" }}
          className={cn("h-full rounded-full bg-gradient-to-r shadow-sm", getGradientClass(percent))}
        />
      </div>
    </div>
  );
}
