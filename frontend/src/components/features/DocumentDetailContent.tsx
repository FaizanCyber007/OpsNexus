"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { motion } from "framer-motion";
import {
  ArrowLeft,
  MessageSquare,
  Bot,
  FileText,
} from "lucide-react";
import { AgentIntelligencePanel } from "@/components/features/AgentIntelligencePanel";
import { DocumentChatPanel } from "@/components/features/DocumentChatPanel";
import { DocumentPreviewPane } from "@/components/features/DocumentPreviewPane";
import { StatusBadge } from "@/components/ui/StatusBadge";
import { useToast } from "@/contexts/ToastContext";
import { useDocumentPolling } from "@/hooks/useDocumentPolling";
import { apiClient } from "@/lib/apiClient";
import type { Answer } from "@/lib/types";
import { cn } from "@/lib/utils";

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
  const [activeTab, setActiveTab] = useState<"chat" | "intelligence">("chat");
  const { showError } = useToast();

  useEffect(() => {
    let cancelled = false;

    async function loadAnswers() {
      setAnswers(null);
      setAnswersError(false);

      if (document?.status !== "completed") return;

      try {
        const result = await apiClient.get<Answer[]>(
          `/documents/${documentId}/answers/`
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

  const fileName = document ? displayName(document.file_path) : "Loading document…";

  return (
    <div className="flex flex-1 flex-col gap-5 overflow-y-auto p-6 sm:p-8">
      {/* Top Breadcrumb & Document Header */}
      <div className="flex flex-wrap items-center justify-between gap-4 border-b border-white/[0.06] pb-4">
        <div className="flex items-center gap-3 min-w-0">
          <Link
            href="/dashboard"
            className="flex h-8 w-8 items-center justify-center rounded-xl border border-white/10 bg-white/[0.03] text-white/60 hover:bg-white/[0.08] hover:text-white transition-all shrink-0"
            aria-label="Back to dashboard"
          >
            <ArrowLeft className="h-4 w-4" />
          </Link>

          <div className="min-w-0">
            <div className="flex items-center gap-2 text-[11px] text-white/40 mb-0.5">
              <span>Dashboard</span>
              <span>/</span>
              <span>Documents</span>
              <span>/</span>
              <span className="font-mono text-white/60 truncate">{documentId.slice(0, 8)}</span>
            </div>
            <h1 className="truncate text-base sm:text-lg font-bold text-white flex items-center gap-2">
              <FileText className="h-4 w-4 text-indigo-400 shrink-0" />
              <span className="truncate">{fileName}</span>
            </h1>
          </div>
        </div>

        {document && (
          <div className="flex items-center gap-2">
            <StatusBadge status={document.status} />
          </div>
        )}
      </div>

      {/* Workbench Dual-Pane Layout */}
      <div className="grid flex-1 grid-cols-1 gap-6 lg:grid-cols-2 min-h-0">
        {/* Left Pane: Document File Preview */}
        <div className="h-full min-h-[30rem] lg:min-h-0">
          <DocumentPreviewPane fileUrl={document?.file ?? null} fileName={fileName} />
        </div>

        {/* Right Pane: Interactive Chat & Intelligence Workspace */}
        <div className="flex flex-col gap-3 min-h-[32rem] lg:min-h-0">
          {/* Tab Controls with Framer Motion active pill */}
          <div className="flex items-center gap-1 rounded-2xl border border-white/[0.08] bg-[#111116]/90 p-1.5 backdrop-blur-xl shadow-lg">
            <button
              type="button"
              onClick={() => setActiveTab("chat")}
              className={cn(
                "relative flex flex-1 items-center justify-center gap-2 rounded-xl py-2 text-xs font-semibold transition-colors",
                activeTab === "chat" ? "text-white" : "text-white/50 hover:text-white/80"
              )}
            >
              {activeTab === "chat" && (
                <motion.div
                  layoutId="detailActiveTab"
                  className="absolute inset-0 rounded-xl bg-gradient-to-r from-indigo-500/25 to-violet-500/25 border border-indigo-500/30 shadow-inner"
                  transition={{ type: "spring", stiffness: 400, damping: 30 }}
                />
              )}
              <span className="relative z-10 flex items-center gap-1.5">
                <MessageSquare className="h-3.5 w-3.5 text-indigo-400" />
                <span>RAG Chat & Model Arena</span>
              </span>
            </button>

            <button
              type="button"
              onClick={() => setActiveTab("intelligence")}
              className={cn(
                "relative flex flex-1 items-center justify-center gap-2 rounded-xl py-2 text-xs font-semibold transition-colors",
                activeTab === "intelligence" ? "text-white" : "text-white/50 hover:text-white/80"
              )}
            >
              {activeTab === "intelligence" && (
                <motion.div
                  layoutId="detailActiveTab"
                  className="absolute inset-0 rounded-xl bg-gradient-to-r from-indigo-500/25 to-violet-500/25 border border-indigo-500/30 shadow-inner"
                  transition={{ type: "spring", stiffness: 400, damping: 30 }}
                />
              )}
              <span className="relative z-10 flex items-center gap-1.5">
                <Bot className="h-3.5 w-3.5 text-violet-400" />
                <span>Agent Intelligence & Trace</span>
              </span>
            </button>
          </div>

          {/* Active Tab Panel */}
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
