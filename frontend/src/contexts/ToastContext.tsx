"use client";

import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useRef,
  useState,
  type ReactNode,
} from "react";
import { AnimatePresence } from "framer-motion";
import { Toast, type ToastItem, type ToastVariant } from "@/components/ui/Toast";

interface ToastOptions {
  duration?: number;
  actionLabel?: string;
  onAction?: () => void;
}

interface ToastContextValue {
  showToast: (message: string, variant?: ToastVariant, options?: ToastOptions) => void;
  showError: (message: string, options?: ToastOptions) => void;
  showSuccess: (message: string, options?: ToastOptions) => void;
  showWarning: (message: string, options?: ToastOptions) => void;
}

const ToastContext = createContext<ToastContextValue | null>(null);

export function ToastProvider({ children }: { children: ReactNode }) {
  const [toasts, setToasts] = useState<ToastItem[]>([]);
  const nextId = useRef(0);
  const timeoutsRef = useRef<Map<string, ReturnType<typeof setTimeout>>>(new Map());

  const dismiss = useCallback((id: string) => {
    const handle = timeoutsRef.current.get(id);
    if (handle) {
      clearTimeout(handle);
      timeoutsRef.current.delete(id);
    }
    setToasts((prev) => prev.filter((toast) => toast.id !== id));
  }, []);

  useEffect(() => {
    const currentTimers = timeoutsRef.current;
    return () => {
      currentTimers.forEach((timer) => clearTimeout(timer));
      currentTimers.clear();
    };
  }, []);

  const showToast = useCallback(
    (message: string, variant: ToastVariant = "info", options?: ToastOptions) => {
      const id = `toast-${nextId.current++}`;
      const duration = options?.duration ?? 5000;
      const newToast: ToastItem = {
        id,
        message,
        variant,
        duration,
        actionLabel: options?.actionLabel,
        onAction: options?.onAction,
      };

      setToasts((prev) => [...prev, newToast]);
      const timer = setTimeout(() => {
        timeoutsRef.current.delete(id);
        dismiss(id);
      }, duration);
      timeoutsRef.current.set(id, timer);
    },
    [dismiss]
  );

  const showError = useCallback(
    (message: string, options?: ToastOptions) => showToast(message, "error", options),
    [showToast]
  );

  const showSuccess = useCallback(
    (message: string, options?: ToastOptions) => showToast(message, "success", options),
    [showToast]
  );

  const showWarning = useCallback(
    (message: string, options?: ToastOptions) => showToast(message, "warning", options),
    [showToast]
  );

  const value = useMemo(
    () => ({ showToast, showError, showSuccess, showWarning }),
    [showToast, showError, showSuccess, showWarning]
  );

  return (
    <ToastContext.Provider value={value}>
      {children}
      <div className="pointer-events-none fixed bottom-5 right-5 z-50 flex w-full max-w-sm flex-col gap-2.5">
        <AnimatePresence mode="popLayout">
          {toasts.map((toast) => (
            <div key={toast.id} className="pointer-events-auto">
              <Toast toast={toast} onDismiss={dismiss} />
            </div>
          ))}
        </AnimatePresence>
      </div>
    </ToastContext.Provider>
  );
}

export function useToast(): ToastContextValue {
  const context = useContext(ToastContext);
  if (!context) {
    throw new Error("useToast must be used within a ToastProvider");
  }
  return context;
}
