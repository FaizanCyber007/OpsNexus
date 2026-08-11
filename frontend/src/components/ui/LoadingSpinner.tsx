const SIZE_CLASSES: Record<"sm" | "md" | "lg", string> = {
  sm: "h-4 w-4 border-2",
  md: "h-6 w-6 border-2",
  lg: "h-10 w-10 border-4",
};

interface LoadingSpinnerProps {
  size?: keyof typeof SIZE_CLASSES;
  className?: string;
}

export function LoadingSpinner({ size = "md", className = "" }: LoadingSpinnerProps) {
  return (
    <div
      role="status"
      aria-label="Loading"
      className={`animate-spin rounded-full border-white/20 border-t-indigo-400 ${SIZE_CLASSES[size]} ${className}`}
    />
  );
}
