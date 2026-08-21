"use client";

import { useEffect, useState } from "react";

import { AgentTraceViewer } from "@/components/features/AgentTraceViewer";
import { Meter } from "@/components/ui/Meter";
import { Shimmer } from "@/components/ui/Shimmer";
import { StatusBadge } from "@/components/ui/StatusBadge";
import { useToast } from "@/contexts/ToastContext";
import { useDocumentPolling } from "@/hooks/useDocumentPolling";
import { apiClient } from "@/lib/apiClient";
import type { Answer, Document } from "@/lib/types";

interface AnswerDisplayProps {
  documentId: string;
  fileName: string;
  onStatusChange?: (status: Document["status"]) => void;
}

export function AnswerDisplay({ documentId, fileName, onStatusChange }: AnswerDisplayProps) {
  const { showError } = useToast();
  const handleStatusChange = (status: Document["status"]) => {
    if (status === "failed") {
      showError(`AI processing failed for "${fileName}".`);
    }
    onStatusChange?.(status);
  };
  const { document, isPolling } = useDocumentPolling(documentId, handleStatusChange);
  const [answers, setAnswers] = useState<Answer[] | null>(null);

  useEffect(() => {
    setAnswers(null);
    if (document?.status !== "completed") return;
    let cancelled = false;
    apiClient
      .get<Answer[]>(`/documents/${documentId}/answers/`)
      .then((data) => {
        if (!cancelled) setAnswers(data);
      })
      .catch(() => {
        if (!cancelled) {
          setAnswers([]);
          showError(`Couldn't load the answer for "${fileName}".`);
        }
      });
    return () => {
      cancelled = true;
    };
  }, [document?.status, documentId, fileName, showError]);

  return (
    <div className="rounded-xl border border-white/10 bg-white/5 p-4">
      <div className="mb-3 flex items-center justify-between gap-3">
        <span className="truncate text-sm font-medium text-white/90">{fileName}</span>
        <StatusBadge status={document?.status ?? "pending"} />
      </div>

      {document?.status === "failed" && (
        <p className="text-sm text-status-critical">
          Processing failed for this document.
        </p>
      )}

      <div className="mb-4">
        <AgentTraceViewer
          agentRunId={document?.latest_agent_run_id ?? null}
          isTerminal={document?.status === "completed" || document?.status === "failed"}
        />
      </div>

      {(isPolling || document?.status === "pending" || document?.status === "processing") && (
        <div className="flex flex-col gap-2">
          <Shimmer className="h-3.5 w-2/3" />
          <Shimmer className="h-3.5 w-full" />
          <Shimmer className="h-3.5 w-5/6" />
        </div>
      )}

      {document?.status === "completed" && answers === null && (
        <div className="flex flex-col gap-2">
          <Shimmer className="h-3.5 w-2/3" />
          <Shimmer className="h-3.5 w-full" />
        </div>
      )}

      {document?.status === "completed" && answers !== null && answers.length === 0 && (
        <p className="text-sm text-white/50">No answer produced for this document.</p>
      )}

      {document?.status === "completed" && answers !== null && answers.length > 0 && (
        <div className="flex flex-col gap-4">
          {answers.map((answer) => (
            <div key={answer.id} className="flex flex-col gap-3">
              <p className="text-sm leading-relaxed text-white/90">{answer.content}</p>
              {answer.confidence_score !== null && (
                <Meter label="Confidence" value={answer.confidence_score} />
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
