import { Loader2 } from "lucide-react";
import { cn } from "@/lib/utils";

const SIZE_CLASSES = {
  xs: "h-3.5 w-3.5",
  sm: "h-4 w-4",
  md: "h-5 w-5",
  lg: "h-7 w-7",
};

interface LoadingSpinnerProps {
  size?: keyof typeof SIZE_CLASSES;
  className?: string;
}

export function LoadingSpinner({ size = "md", className = "" }: LoadingSpinnerProps) {
  return (
    <Loader2
      role="status"
      aria-label="Loading"
      className={cn("animate-spin text-indigo-400 shrink-0", SIZE_CLASSES[size], className)}
    />
  );
}
