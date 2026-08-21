import { cn } from "@/lib/utils";

interface SkeletonProps {
  className?: string;
}

export function Skeleton({ className = "h-4 w-full" }: SkeletonProps) {
  return (
    <div
      aria-hidden="true"
      className={cn(
        "rounded-lg bg-[linear-gradient(90deg,rgba(255,255,255,0.03)_20%,rgba(255,255,255,0.08)_50%,rgba(255,255,255,0.03)_80%)] bg-[length:250%_100%] [animation:shimmer_2s_infinite_linear]",
        className
      )}
    />
  );
}

export function TableSkeleton({ rows = 4 }: { rows?: number }) {
  return (
    <div className="w-full space-y-3 p-4">
      {/* Header bar skeleton */}
      <div className="flex items-center justify-between pb-3 border-b border-white/[0.06]">
        <Skeleton className="h-4 w-28" />
        <Skeleton className="h-4 w-20" />
        <Skeleton className="h-4 w-24" />
        <Skeleton className="h-4 w-16" />
      </div>

      {/* Row skeletons */}
      {Array.from({ length: rows }).map((_, idx) => (
        <div key={idx} className="flex items-center justify-between py-2.5 border-b border-white/[0.03] last:border-b-0">
          <div className="flex items-center gap-3 w-1/3">
            <Skeleton className="h-4 w-4 rounded" />
            <Skeleton className="h-4 w-4/5" />
          </div>
          <Skeleton className="h-5 w-24 rounded-full" />
          <Skeleton className="h-5 w-20 rounded-full" />
          <Skeleton className="h-4 w-28" />
          <Skeleton className="h-6 w-6 rounded-md" />
        </div>
      ))}
    </div>
  );
}

export function ChatBubbleSkeleton({ isArena = false }: { isArena?: boolean }) {
  if (isArena) {
    return (
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4 py-2">
        <div className="rounded-xl border border-amber-500/20 bg-amber-950/10 p-4 space-y-3">
          <div className="flex items-center justify-between pb-2 border-b border-amber-500/10">
            <Skeleton className="h-4 w-32 bg-amber-500/10" />
            <Skeleton className="h-4 w-14 bg-amber-500/10 rounded-full" />
          </div>
          <Skeleton className="h-3.5 w-5/6 bg-amber-500/10" />
          <Skeleton className="h-3.5 w-full bg-amber-500/10" />
          <Skeleton className="h-3.5 w-4/5 bg-amber-500/10" />
          <Skeleton className="h-3.5 w-2/3 bg-amber-500/10" />
        </div>

        <div className="rounded-xl border border-indigo-500/20 bg-indigo-950/10 p-4 space-y-3">
          <div className="flex items-center justify-between pb-2 border-b border-indigo-500/10">
            <Skeleton className="h-4 w-28 bg-indigo-500/10" />
            <Skeleton className="h-4 w-14 bg-indigo-500/10 rounded-full" />
          </div>
          <Skeleton className="h-3.5 w-4/5 bg-indigo-500/10" />
          <Skeleton className="h-3.5 w-full bg-indigo-500/10" />
          <Skeleton className="h-3.5 w-11/12 bg-indigo-500/10" />
          <Skeleton className="h-3.5 w-3/4 bg-indigo-500/10" />
        </div>
      </div>
    );
  }

  return (
    <div className="rounded-xl border border-white/10 bg-white/[0.03] p-4 space-y-3">
      <div className="flex items-center justify-between pb-2 border-b border-white/5">
        <Skeleton className="h-4 w-24" />
        <Skeleton className="h-4 w-12" />
      </div>
      <Skeleton className="h-3.5 w-4/5" />
      <Skeleton className="h-3.5 w-full" />
      <Skeleton className="h-3.5 w-3/4" />
    </div>
  );
}

export function IntelligenceSkeleton() {
  return (
    <div className="space-y-5 p-1">
      <div className="space-y-2">
        <Skeleton className="h-3.5 w-1/4" />
        <Skeleton className="h-4 w-full" />
        <Skeleton className="h-4 w-5/6" />
      </div>

      <div className="space-y-2">
        <Skeleton className="h-3 w-20" />
        <Skeleton className="h-2 w-full rounded-full" />
      </div>

      <div className="space-y-2">
        <Skeleton className="h-3 w-24" />
        <div className="flex gap-2">
          <Skeleton className="h-6 w-24 rounded-full" />
          <Skeleton className="h-6 w-28 rounded-full" />
        </div>
      </div>

      <div className="space-y-2">
        <Skeleton className="h-3 w-28" />
        <Skeleton className="h-9 w-full rounded-lg" />
        <Skeleton className="h-9 w-full rounded-lg" />
      </div>
    </div>
  );
}
