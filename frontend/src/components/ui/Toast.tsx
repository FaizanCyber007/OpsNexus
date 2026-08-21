"use client";

import { useEffect, useState } from "react";
import { motion } from "framer-motion";
import { AlertCircle, CheckCircle2, Info, AlertTriangle, X } from "lucide-react";
import { cn } from "@/lib/utils";

export type ToastVariant = "error" | "success" | "info" | "warning";

export interface ToastItem {
  id: string;
  message: string;
  variant: ToastVariant;
  duration?: number;
  actionLabel?: string;
  onAction?: () => void;
}

const VARIANT_CONFIG: Record<
  ToastVariant,
  { borderClass: string; bgClass: string; textClass: string; icon: typeof AlertCircle }
> = {
  error: {
    borderClass: "border-rose-500/30",
    bgClass: "bg-[#181114]/95",
    textClass: "text-rose-400",
    icon: AlertCircle,
  },
  success: {
    borderClass: "border-emerald-500/30",
    bgClass: "bg-[#101814]/95",
    textClass: "text-emerald-400",
    icon: CheckCircle2,
  },
  warning: {
    borderClass: "border-amber-500/30",
    bgClass: "bg-[#181610]/95",
    textClass: "text-amber-400",
    icon: AlertTriangle,
  },
  info: {
    borderClass: "border-indigo-500/30",
    bgClass: "bg-[#12141c]/95",
    textClass: "text-indigo-400",
    icon: Info,
  },
};

interface ToastProps {
  toast: ToastItem;
  onDismiss: (id: string) => void;
}

export function Toast({ toast, onDismiss }: ToastProps) {
  const { borderClass, bgClass, textClass, icon: Icon } = VARIANT_CONFIG[toast.variant];
  const duration = toast.duration ?? 5000;
  const [progress, setProgress] = useState(100);

  useEffect(() => {
    const startTime = Date.now();
    const interval = setInterval(() => {
      const elapsed = Date.now() - startTime;
      const remaining = Math.max(0, 100 - (elapsed / duration) * 100);
      setProgress(remaining);
      if (remaining <= 0) clearInterval(interval);
    }, 40);

    return () => clearInterval(interval);
  }, [duration]);

  return (
    <motion.div
      layout
      initial={{ opacity: 0, y: 20, scale: 0.95 }}
      animate={{ opacity: 1, y: 0, scale: 1 }}
      exit={{ opacity: 0, y: -10, scale: 0.9, transition: { duration: 0.2 } }}
      role="alert"
      className={cn(
        "relative flex flex-col overflow-hidden rounded-2xl border p-4 shadow-2xl backdrop-blur-xl transition-all",
        borderClass,
        bgClass
      )}
    >
      <div className="flex items-start gap-3">
        <div className={cn("mt-0.5 shrink-0 rounded-lg p-1", textClass)}>
          <Icon className="h-4 w-4" />
        </div>

        <div className="flex-1 pr-2">
          <p className="text-xs font-medium leading-relaxed text-white/90">
            {toast.message}
          </p>

          {toast.actionLabel && (
            <button
              type="button"
              onClick={() => {
                toast.onAction?.();
                onDismiss(toast.id);
              }}
              className="mt-2 text-xs font-semibold text-indigo-400 hover:text-indigo-300 underline"
            >
              {toast.actionLabel}
            </button>
          )}
        </div>

        <button
          type="button"
          onClick={() => onDismiss(toast.id)}
          aria-label="Dismiss"
          className="shrink-0 text-white/40 hover:text-white/80 p-0.5 rounded transition-colors"
        >
          <X className="h-3.5 w-3.5" />
        </button>
      </div>

      {/* Countdown Progress Bar */}
      <div className="absolute bottom-0 left-0 right-0 h-0.5 bg-white/5">
        <div
          className={cn("h-full transition-all duration-75", textClass.replace("text-", "bg-"))}
          style={{ width: `${progress}%` }}
        />
      </div>
    </motion.div>
  );
}
