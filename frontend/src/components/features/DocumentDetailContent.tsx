"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

import { AgentIntelligencePanel } from "@/components/features/AgentIntelligencePanel";
import { DocumentChatPanel } from "@/components/features/DocumentChatPanel";
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
  const [answersError, setAnswersError] = useState(false);
  const [activeTab, setActiveTab] = useState<"intelligence" | "chat">("chat");
  const { showError } = useToast();

  useEffect(() => {
    let cancelled = false;

    async function loadAnswers() {
      // Reset immediately so a previously viewed document's stale answers
      // (or error state) never linger while this document's own fetch is
      // still pending.
      setAnswers(null);
      setAnswersError(false);

      if (document?.status !== "completed") return;

      try {
        const result = await apiClient.get<Answer[]>(
          `/documents/${documentId}/answers/`,
        );
        if (cancelled) return;
        setAnswers(result);
      } catch {
        if (cancelled) return;
        setAnswersError(true);
        showError("Couldn't load the answer for this document.");
      }
    }

    loadAnswers();

    return () => {
      cancelled = true;
    };
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

        <div className="flex flex-col gap-3 min-h-[30rem] lg:min-h-0">
          {/* Tab Navigation Controls */}
          <div className="flex items-center gap-2 rounded-xl border border-white/10 bg-white/5 p-1 backdrop-blur-md">
            <button
              type="button"
              onClick={() => setActiveTab("chat")}
              className={`flex-1 flex items-center justify-center gap-2 rounded-lg py-2 text-xs font-medium transition-all ${
                activeTab === "chat"
                  ? "bg-indigo-600 text-white shadow-md font-semibold"
                  : "text-white/60 hover:text-white hover:bg-white/5"
              }`}
            >
              <span>💬 Document Chat & Arena</span>
            </button>
            <button
              type="button"
              onClick={() => setActiveTab("intelligence")}
              className={`flex-1 flex items-center justify-center gap-2 rounded-lg py-2 text-xs font-medium transition-all ${
                activeTab === "intelligence"
                  ? "bg-indigo-600 text-white shadow-md font-semibold"
                  : "text-white/60 hover:text-white hover:bg-white/5"
              }`}
            >
              <span>📊 Agent Intelligence</span>
            </button>
          </div>

          {/* Active Tab View */}
          <div className="flex-1 min-h-0">
            {activeTab === "chat" ? (
              <DocumentChatPanel document={document} documentId={documentId} />
            ) : (
              <AgentIntelligencePanel
                document={document}
                answers={answers}
                answersError={answersError}
              />
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
