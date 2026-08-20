interface ShimmerProps {
  className?: string;
}

export function Shimmer({ className = "h-4 w-full" }: ShimmerProps) {
  return (
    <div
      className={`rounded-md bg-[linear-gradient(90deg,rgba(255,255,255,0.06)_25%,rgba(255,255,255,0.16)_37%,rgba(255,255,255,0.06)_63%)] bg-[length:400%_100%] [animation:shimmer_1.6s_ease-in-out_infinite] ${className}`}
    />
  );
}
