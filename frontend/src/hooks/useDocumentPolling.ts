"use client";

import { useEffect, useRef, useState } from "react";

import { useToast } from "@/contexts/ToastContext";
import { apiClient } from "@/lib/apiClient";
import type { Document } from "@/lib/types";

const POLL_INTERVAL_MS = 1500;
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

    async function poll() {
      try {
        const result = await apiClient.get<Document>(`/documents/${documentId}/`);
        if (cancelled) return;

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
        if (!cancelled) {
          setIsPolling(false);
          showError("Lost connection while checking document status.");
        }
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
