"use client";

import { useEffect, useState } from "react";
import { FileText, AlertCircle, Sparkles } from "lucide-react";
import { AgentTraceViewer } from "@/components/features/AgentTraceViewer";
import { Meter } from "@/components/ui/Meter";
import { Skeleton } from "@/components/ui/Skeleton";
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

export function AnswerDisplay({
  documentId,
  fileName,
  onStatusChange,
}: AnswerDisplayProps) {
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

  const isPending =
    isPolling || document?.status === "pending" || document?.status === "processing";

  return (
    <div className="rounded-2xl border border-white/[0.08] bg-[#111116]/90 p-5 shadow-xl backdrop-blur-xl transition-all">
      {/* Header bar */}
      <div className="mb-3.5 flex items-center justify-between gap-3">
        <div className="flex items-center gap-2 truncate">
          <FileText className="h-4 w-4 text-indigo-400 shrink-0" />
          <span className="truncate text-xs font-semibold text-white/90">{fileName}</span>
        </div>
        <StatusBadge status={document?.status ?? "pending"} size="sm" />
      </div>

      {/* Failure message */}
      {document?.status === "failed" && (
        <div className="mb-3 rounded-xl border border-rose-500/30 bg-rose-500/10 p-3 text-xs text-rose-300 space-y-1">
          <div className="flex items-center gap-2">
            <AlertCircle className="h-4 w-4 shrink-0" />
            <span className="font-semibold">Processing failed</span>
          </div>
          {document.latest_agent_run_error && (
            <p className="text-rose-200/80 leading-relaxed pl-6 break-words">
              {document.latest_agent_run_error}
            </p>
          )}
        </div>
      )}

      {/* Embedded Agent Trace */}
      <div className="mb-3">
        <AgentTraceViewer
          agentRunId={document?.latest_agent_run_id ?? null}
          isTerminal={document?.status === "completed" || document?.status === "failed"}
        />
      </div>

      {/* Pending Shimmer Loading State */}
      {isPending && (
        <div className="space-y-2 py-2">
          <div className="flex items-center gap-1.5 text-xs text-amber-300">
            <Sparkles className="h-3.5 w-3.5 animate-spin text-amber-400" />
            <span>Autonomous agent workflow in progress…</span>
          </div>
          <Skeleton className="h-3 w-3/4" />
          <Skeleton className="h-3 w-full" />
          <Skeleton className="h-3 w-5/6" />
        </div>
      )}

      {/* Completed Results */}
      {document?.status === "completed" && answers === null && (
        <div className="space-y-2 py-2">
          <Skeleton className="h-3 w-2/3" />
          <Skeleton className="h-3 w-full" />
        </div>
      )}

      {document?.status === "completed" && answers !== null && answers.length === 0 && (
        <p className="text-xs text-white/40 italic">No answer payload returned by worker agent.</p>
      )}

      {document?.status === "completed" && answers !== null && answers.length > 0 && (
        <div className="space-y-3 pt-2">
          {answers.map((answer) => (
            <div key={answer.id} className="space-y-3 rounded-xl bg-white/[0.02] p-3 border border-white/[0.04]">
              <p className="text-xs leading-relaxed text-white/90">{answer.content}</p>
              {answer.confidence_score !== null && (
                <Meter label="Resolution Confidence" value={answer.confidence_score} />
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
