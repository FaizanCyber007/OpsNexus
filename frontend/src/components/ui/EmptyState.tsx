import type { ReactNode } from "react";
import { FolderOpen } from "lucide-react";
import { Button } from "@/components/ui/Button";
import { cn } from "@/lib/utils";

interface EmptyStateProps {
  icon?: ReactNode;
  title: string;
  description: string;
  actionLabel?: string;
  onAction?: () => void;
  secondaryActionLabel?: string;
  onSecondaryAction?: () => void;
  className?: string;
}

export function EmptyState({
  icon,
  title,
  description,
  actionLabel,
  onAction,
  secondaryActionLabel,
  onSecondaryAction,
  className = "",
}: EmptyStateProps) {
  return (
    <div
      className={cn(
        "flex flex-col items-center justify-center rounded-2xl border-2 border-dashed border-white/[0.08] bg-[#111116]/40 px-6 py-12 text-center backdrop-blur-md transition-all hover:border-white/[0.14]",
        className
      )}
    >
      <div className="flex h-12 w-12 items-center justify-center rounded-2xl border border-white/10 bg-white/[0.04] text-indigo-400 shadow-inner mb-4">
        {icon || <FolderOpen className="h-6 w-6 stroke-[1.5]" />}
      </div>

      <h4 className="text-base font-semibold text-white/90">{title}</h4>
      <p className="mt-1.5 max-w-sm text-xs text-white/50 leading-relaxed">
        {description}
      </p>

      {(actionLabel || secondaryActionLabel) && (
        <div className="mt-6 flex flex-wrap items-center justify-center gap-3">
          {secondaryActionLabel && (
            <Button variant="secondary" size="sm" onClick={onSecondaryAction}>
              {secondaryActionLabel}
            </Button>
          )}
          {actionLabel && (
            <Button variant="primary" size="sm" onClick={onAction}>
              {actionLabel}
            </Button>
          )}
        </div>
      )}
    </div>
  );
}
