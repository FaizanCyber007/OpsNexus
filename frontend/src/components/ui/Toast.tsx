export type ToastVariant = "error" | "info";

export interface ToastItem {
  id: string;
  message: string;
  variant: ToastVariant;
}

const VARIANT_CONFIG: Record<ToastVariant, { className: string; icon: "cross" | "info" }> = {
  error: {
    className: "border-status-critical/30 bg-status-critical/10 text-status-critical",
    icon: "cross",
  },
  info: {
    className: "border-status-warning/30 bg-status-warning/10 text-status-warning",
    icon: "info",
  },
};

interface ToastProps {
  toast: ToastItem;
  onDismiss: (id: string) => void;
}

export function Toast({ toast, onDismiss }: ToastProps) {
  const { className, icon } = VARIANT_CONFIG[toast.variant];

  return (
    <div
      role="alert"
      className={`flex items-start gap-2.5 rounded-xl border px-4 py-3 text-sm shadow-2xl backdrop-blur-xl ${className}`}
    >
      {icon === "cross" && (
        <svg viewBox="0 0 16 16" className="mt-0.5 h-4 w-4 shrink-0" fill="none">
          <circle cx="8" cy="8" r="7" stroke="currentColor" strokeWidth="1.5" />
          <path
            d="M5.5 5.5 10.5 10.5M10.5 5.5 5.5 10.5"
            stroke="currentColor"
            strokeWidth="1.5"
            strokeLinecap="round"
          />
        </svg>
      )}
      {icon === "info" && (
        <svg viewBox="0 0 16 16" className="mt-0.5 h-4 w-4 shrink-0" fill="none">
          <circle cx="8" cy="8" r="7" stroke="currentColor" strokeWidth="1.5" />
          <path d="M8 7v4.5" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" />
          <circle cx="8" cy="4.75" r="0.9" fill="currentColor" />
        </svg>
      )}
      <p className="flex-1 leading-snug text-white/90">{toast.message}</p>
      <button
        type="button"
        onClick={() => onDismiss(toast.id)}
        aria-label="Dismiss"
        className="text-white/40 transition-colors hover:text-white/80"
      >
        <svg viewBox="0 0 16 16" className="h-3.5 w-3.5" fill="none">
          <path
            d="M4 4 12 12M12 4 4 12"
            stroke="currentColor"
            strokeWidth="1.5"
            strokeLinecap="round"
          />
        </svg>
      </button>
    </div>
  );
}
