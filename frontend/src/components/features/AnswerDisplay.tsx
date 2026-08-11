"use client";

import { useEffect, useState } from "react";

import { Shimmer } from "@/components/ui/Shimmer";
import { useDocumentPolling } from "@/hooks/useDocumentPolling";
import { apiClient } from "@/lib/apiClient";
import type { Answer } from "@/lib/types";

interface AnswerDisplayProps {
  documentId: string;
}

export function AnswerDisplay({ documentId }: AnswerDisplayProps) {
  const { document, isPolling } = useDocumentPolling(documentId);
  const [answers, setAnswers] = useState<Answer[] | null>(null);

  useEffect(() => {
    if (document?.status !== "completed") return;
    apiClient
      .get<Answer[]>(`/documents/${documentId}/answers/`)
      .then(setAnswers)
      .catch(() => setAnswers([]));
  }, [document?.status, documentId]);

  if (document?.status === "failed") {
    return (
      <div className="rounded-lg border border-red-500/30 bg-red-500/10 px-4 py-3 text-sm text-red-300">
        Processing failed for this document.
      </div>
    );
  }

  if (isPolling || document?.status !== "completed" || answers === null) {
    return (
      <div className="flex flex-col gap-2 rounded-lg border border-white/10 bg-white/5 p-4">
        <Shimmer className="h-4 w-2/3" />
        <Shimmer className="h-4 w-full" />
        <Shimmer className="h-4 w-5/6" />
      </div>
    );
  }

  if (answers.length === 0) {
    return (
      <div className="rounded-lg border border-white/10 bg-white/5 px-4 py-3 text-sm text-white/50">
        No answer produced for this document.
      </div>
    );
  }

  return (
    <div className="flex flex-col gap-2">
      {answers.map((answer) => (
        <div
          key={answer.id}
          className="rounded-lg border border-white/10 bg-white/5 p-4 text-sm text-white/90"
        >
          <p>{answer.content}</p>
          {answer.confidence_score !== null && (
            <p className="mt-2 text-xs text-white/50">
              Confidence: {Math.round(answer.confidence_score * 100)}%
            </p>
          )}
        </div>
      ))}
    </div>
  );
}
