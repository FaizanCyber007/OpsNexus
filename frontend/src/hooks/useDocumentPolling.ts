"use client";

import { useEffect, useRef, useState } from "react";
import { useToast } from "@/contexts/ToastContext";
import { apiClient } from "@/lib/apiClient";
import type { Document } from "@/lib/types";

const POLL_INTERVAL_MS = 1500;
const MAX_POLL_BACKOFF_MS = 15000;
const MAX_CONSECUTIVE_FAILURES = 5;
const TERMINAL_STATUSES: Document["status"][] = ["completed", "failed"];

export function useDocumentPolling(
  documentId: string,
  onStatusChange?: (status: Document["status"]) => void,
) {
  const [document, setDocument] = useState<Document | null>(null);
  const [isPolling, setIsPolling] = useState(true);
  const onStatusChangeRef = useRef(onStatusChange);
  const { showError } = useToast();

  useEffect(() => {
    onStatusChangeRef.current = onStatusChange;
  });

  useEffect(() => {
    let cancelled = false;
    let timeoutId: ReturnType<typeof setTimeout>;
    let lastStatus: Document["status"] | null = null;
    let consecutiveFailures = 0;

    async function poll() {
      try {
        const result = await apiClient.get<Document>(`/documents/${documentId}/`);
        if (cancelled) return;

        consecutiveFailures = 0;
        setDocument(result);
        if (result.status !== lastStatus) {
          lastStatus = result.status;
          onStatusChangeRef.current?.(result.status);
        }

        if (TERMINAL_STATUSES.includes(result.status)) {
          setIsPolling(false);
          return;
        }

        timeoutId = setTimeout(poll, POLL_INTERVAL_MS);
      } catch {
        if (cancelled) return;

        consecutiveFailures += 1;
        if (consecutiveFailures >= MAX_CONSECUTIVE_FAILURES) {
          setIsPolling(false);
          showError("Lost connection while checking document status.");
          return;
        }

        const delay = Math.min(
          POLL_INTERVAL_MS * 2 ** consecutiveFailures,
          MAX_POLL_BACKOFF_MS,
        );
        timeoutId = setTimeout(poll, delay);
      }
    }

    poll();

    return () => {
      cancelled = true;
      clearTimeout(timeoutId);
    };
  }, [documentId, showError]);

  return { document, isPolling };
}
