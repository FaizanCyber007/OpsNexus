"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

import { AgentIntelligencePanel } from "@/components/features/AgentIntelligencePanel";
import { DocumentPreviewPane } from "@/components/features/DocumentPreviewPane";
import { StatusBadge } from "@/components/ui/StatusBadge";
import { useToast } from "@/contexts/ToastContext";
import { useDocumentPolling } from "@/hooks/useDocumentPolling";
import { apiClient } from "@/lib/apiClient";
import type { Answer } from "@/lib/types";

interface DocumentDetailContentProps {
  documentId: string;
}

function displayName(filePath: string): string {
  return filePath.split("/").pop() || "Untitled document";
}

export function DocumentDetailContent({ documentId }: DocumentDetailContentProps) {
  const { document } = useDocumentPolling(documentId);
  const [answers, setAnswers] = useState<Answer[] | null>(null);
  const { showError } = useToast();

  useEffect(() => {
    if (document?.status !== "completed") return;
    apiClient
      .get<Answer[]>(`/documents/${documentId}/answers/`)
      .then(setAnswers)
      .catch(() => {
        setAnswers([]);
        showError("Couldn't load the answer for this document.");
      });
  }, [document?.status, documentId, showError]);

  const fileName = document ? displayName(document.file_path) : "Loading…";

  return (
    <div className="flex flex-1 flex-col gap-6 overflow-y-auto p-10">
      <div className="flex items-center justify-between gap-3">
        <div className="flex items-center gap-3">
          <Link
            href="/dashboard"
            className="text-sm text-white/50 hover:text-white/80"
            aria-label="Back to dashboard"
          >
            ← Back
          </Link>
          <h1 className="truncate text-lg font-semibold text-white">{fileName}</h1>
        </div>
        {document && <StatusBadge status={document.status} />}
      </div>

      <div className="grid flex-1 grid-cols-1 gap-6 lg:grid-cols-2">
        <DocumentPreviewPane fileUrl={document?.file ?? null} fileName={fileName} />
        <AgentIntelligencePanel document={document} answers={answers} />
      </div>
    </div>
  );
}
