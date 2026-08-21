import { Skeleton } from "./Skeleton";

export function Shimmer({ className = "h-4 w-full" }: { className?: string }) {
  return <Skeleton className={className} />;
}
