"use client";

import { useEffect, useState } from "react";

import { apiClient } from "@/lib/apiClient";
import type { Document } from "@/lib/types";

const POLL_INTERVAL_MS = 1500;
const TERMINAL_STATUSES: Document["status"][] = ["completed", "failed"];

export function useDocumentPolling(documentId: string) {
  const [document, setDocument] = useState<Document | null>(null);
  const [isPolling, setIsPolling] = useState(true);

  useEffect(() => {
    let cancelled = false;
    let timeoutId: ReturnType<typeof setTimeout>;

    async function poll() {
      try {
        const result = await apiClient.get<Document>(`/documents/${documentId}/`);
        if (cancelled) return;

        setDocument(result);

        if (TERMINAL_STATUSES.includes(result.status)) {
          setIsPolling(false);
          return;
        }

        timeoutId = setTimeout(poll, POLL_INTERVAL_MS);
      } catch {
        if (!cancelled) setIsPolling(false);
      }
    }

    poll();

    return () => {
      cancelled = true;
      clearTimeout(timeoutId);
    };
  }, [documentId]);

  return { document, isPolling };
}
