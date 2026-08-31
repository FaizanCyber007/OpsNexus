"use client";

import { useEffect, useRef, useState } from "react";
import { useToast } from "@/contexts/ToastContext";
import { apiClient } from "@/lib/apiClient";
import type { Document } from "@/lib/types";

const POLL_INTERVAL_MS = 1500;
const MAX_POLL_BACKOFF_MS = 15000;
const MAX_CONSECUTIVE_FAILURES = 5;
const TERMINAL_STATUSES: Document["status"][] = ["completed", "failed"];

/** Hard ceiling: stop polling after 5 minutes regardless of status. */
const MAX_POLL_DURATION_MS = 5 * 60 * 1000;

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
    const startTime = Date.now();

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

        // Safety ceiling: stop polling if we've been going too long
        if (Date.now() - startTime >= MAX_POLL_DURATION_MS) {
          setIsPolling(false);
          showError("Document processing is taking longer than expected.");
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
