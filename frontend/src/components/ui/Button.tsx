"use client";

import { forwardRef, type ButtonHTMLAttributes, type ReactNode } from "react";
import { motion, type HTMLMotionProps } from "framer-motion";
import { LoadingSpinner } from "@/components/ui/LoadingSpinner";
import { cn } from "@/lib/utils";

type ButtonVariant = "primary" | "secondary" | "outline" | "ghost" | "destructive";
type ButtonSize = "xs" | "sm" | "md" | "lg";

export interface ButtonProps
  extends Omit<ButtonHTMLAttributes<HTMLButtonElement>, "onAnimationStart" | "onDrag" | "onDragStart" | "onDragEnd"> {
  variant?: ButtonVariant;
  size?: ButtonSize;
  isLoading?: boolean;
  leftIcon?: ReactNode;
  rightIcon?: ReactNode;
}

const VARIANT_CLASSES: Record<ButtonVariant, string> = {
  primary:
    "bg-gradient-to-r from-indigo-500 via-indigo-600 to-violet-600 text-white shadow-lg shadow-indigo-500/25 hover:from-indigo-400 hover:via-indigo-500 hover:to-violet-500 border border-white/10 active:shadow-none",
  secondary:
    "bg-white/[0.06] text-white/90 hover:bg-white/[0.12] hover:text-white border border-white/10 shadow-sm",
  outline:
    "bg-transparent text-white/80 hover:bg-white/5 hover:text-white border border-white/20",
  ghost:
    "bg-transparent text-white/70 hover:bg-white/5 hover:text-white border border-transparent",
  destructive:
    "bg-rose-500/15 text-rose-300 hover:bg-rose-500/25 border border-rose-500/30",
};

const SIZE_CLASSES: Record<ButtonSize, string> = {
  xs: "px-2 py-1 text-xs gap-1.5 rounded-md",
  sm: "px-3 py-1.5 text-xs font-medium gap-1.5 rounded-lg",
  md: "px-4 py-2 text-sm font-medium gap-2 rounded-xl",
  lg: "px-5 py-2.5 text-base font-medium gap-2.5 rounded-xl",
};

export const Button = forwardRef<HTMLButtonElement, ButtonProps>(
  (
    {
      children,
      variant = "primary",
      size = "md",
      isLoading = false,
      leftIcon,
      rightIcon,
      className,
      disabled,
      type = "button",
      ...props
    },
    ref
  ) => {
    const isDisabled = disabled || isLoading;

    return (
      <motion.button
        ref={ref}
        type={type}
        disabled={isDisabled}
        whileHover={isDisabled ? undefined : { scale: 1.015 }}
        whileTap={isDisabled ? undefined : { scale: 0.985 }}
        transition={{ type: "spring", stiffness: 400, damping: 25 }}
        className={cn(
          "relative inline-flex items-center justify-center font-medium transition-colors select-none focus:outline-none focus-visible:ring-2 focus-visible:ring-indigo-400/50 disabled:cursor-not-allowed disabled:opacity-50",
          VARIANT_CLASSES[variant],
          SIZE_CLASSES[size],
          className
        )}
        {...(props as HTMLMotionProps<"button">)}
      >
        {isLoading ? (
          <LoadingSpinner size={size === "lg" ? "md" : "sm"} className="text-current" />
        ) : (
          leftIcon && <span className="shrink-0">{leftIcon}</span>
        )}
        <span>{children}</span>
        {!isLoading && rightIcon && <span className="shrink-0">{rightIcon}</span>}
      </motion.button>
    );
  }
);

Button.displayName = "Button";
