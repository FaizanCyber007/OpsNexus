import { type HTMLAttributes, forwardRef, type ReactNode } from "react";
import { cn } from "@/lib/utils";

export interface CardProps extends HTMLAttributes<HTMLDivElement> {
  children: ReactNode;
  className?: string;
  variant?: "default" | "elevated" | "interactive";
}

export const Card = forwardRef<HTMLDivElement, CardProps>(
  ({ children, className = "", variant = "default", ...props }, ref) => {
    return (
      <div
        ref={ref}
        className={cn(
          "relative overflow-hidden rounded-2xl border border-white/[0.08] bg-[#111116]/80 p-6 shadow-xl backdrop-blur-xl transition-all duration-200",
          variant === "elevated" && "bg-[#16161d]/90 shadow-2xl border-white/[0.12]",
          variant === "interactive" && "hover:border-white/20 hover:bg-[#14141a]/90 hover:shadow-indigo-500/5",
          className
        )}
        {...props}
      >
        {children}
      </div>
    );
  }
);

Card.displayName = "Card";

export function CardHeader({
  children,
  className = "",
}: {
  children: ReactNode;
  className?: string;
}) {
  return (
    <div className={cn("flex flex-col space-y-1.5 pb-4 border-b border-white/[0.06]", className)}>
      {children}
    </div>
  );
}

export function CardTitle({
  children,
  className = "",
}: {
  children: ReactNode;
  className?: string;
}) {
  return (
    <h3 className={cn("text-base font-semibold tracking-tight text-white/95", className)}>
      {children}
    </h3>
  );
}

export function CardDescription({
  children,
  className = "",
}: {
  children: ReactNode;
  className?: string;
}) {
  return (
    <p className={cn("text-xs text-white/50 leading-relaxed", className)}>
      {children}
    </p>
  );
}

export function CardContent({
  children,
  className = "",
}: {
  children: ReactNode;
  className?: string;
}) {
  return <div className={cn("pt-4", className)}>{children}</div>;
}
