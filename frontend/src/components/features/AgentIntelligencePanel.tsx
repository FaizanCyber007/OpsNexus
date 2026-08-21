"use client";

import { useState } from "react";
import {
  Bot,
  ShieldAlert,
  ListTodo,
  ChevronDown,
  ChevronUp,
  FileSearch,
  Sparkles,
  AlertCircle,
  Copy,
  CheckCheck,
} from "lucide-react";
import { Card } from "@/components/ui/Card";
import { ActionItemChecklist } from "@/components/ui/ActionItemChecklist";
import { Meter } from "@/components/ui/Meter";
import { RiskBadge } from "@/components/ui/RiskBadge";
import { IntelligenceSkeleton } from "@/components/ui/Skeleton";
import { EmptyState } from "@/components/ui/EmptyState";
import { AgentTraceViewer } from "@/components/features/AgentTraceViewer";
import type { Answer, Document } from "@/lib/types";

interface AgentIntelligencePanelProps {
  document: Document | null;
  answers: Answer[] | null;
  answersError: boolean;
}

function FullResponseDisclosure({ content }: { content: string }) {
  const [isOpen, setIsOpen] = useState(false);
  const [copied, setCopied] = useState(false);

  const copyContent = () => {
    navigator.clipboard.writeText(content);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="rounded-xl border border-white/[0.08] bg-white/[0.02] p-3 text-xs">
      <div className="flex items-center justify-between">
        <button
          type="button"
          onClick={() => setIsOpen((prev) => !prev)}
          className="inline-flex items-center gap-1.5 font-medium text-indigo-300 hover:text-indigo-200 transition-colors"
        >
          <span>{isOpen ? "Collapse Raw Model Output" : "View Full Model Raw Output"}</span>
          {isOpen ? <ChevronUp className="h-3.5 w-3.5" /> : <ChevronDown className="h-3.5 w-3.5" />}
        </button>

        {isOpen && (
          <button
            type="button"
            onClick={copyContent}
            className="flex items-center gap-1 text-[11px] text-white/40 hover:text-white transition-colors"
          >
            {copied ? (
              <>
                <CheckCheck className="h-3 w-3 text-emerald-400" />
                <span className="text-emerald-400">Copied</span>
              </>
            ) : (
              <>
                <Copy className="h-3 w-3" />
                <span>Copy</span>
              </>
            )}
          </button>
        )}
      </div>

      {isOpen && (
        <div className="mt-3 rounded-lg bg-black/40 p-3 border border-white/5">
          <p className="whitespace-pre-wrap font-mono text-[11px] leading-relaxed text-white/70">
            {content}
          </p>
        </div>
      )}
    </div>
  );
}

export function AgentIntelligencePanel({
  document,
  answers,
  answersError,
}: AgentIntelligencePanelProps) {
  const isPending =
    !document || document.status === "pending" || document.status === "processing";
  const isCompleted = document?.status === "completed";

  return (
    <Card className="flex h-full min-h-[28rem] flex-col gap-4 overflow-y-auto p-5">
      {/* Panel Header */}
      <div className="flex items-center justify-between border-b border-white/[0.06] pb-3">
        <div className="flex items-center gap-2">
          <div className="flex h-7 w-7 items-center justify-center rounded-lg bg-gradient-to-br from-indigo-500/20 to-violet-500/20 text-indigo-300 border border-white/10">
            <Bot className="h-4 w-4" />
          </div>
          <div>
            <h2 className="text-xs font-semibold text-white/90">Agent Intelligence Report</h2>
            <p className="text-[10px] text-white/40 font-mono">
              Multi-Agent Orchestration & Extraction
            </p>
          </div>
        </div>
      </div>

      {/* Embedded Live Tool Trace Timeline */}
      {document?.latest_agent_run_id && (
        <div className="mb-1">
          <AgentTraceViewer
            agentRunId={document.latest_agent_run_id}
            isTerminal={document.status === "completed" || document.status === "failed"}
          />
        </div>
      )}

      {/* Loading & Pending Shimmer */}
      {isPending && (
        <div className="space-y-4 py-2">
          <div className="flex items-center gap-2 text-xs text-amber-300">
            <Sparkles className="h-4 w-4 animate-spin text-amber-400" />
            <span>AI Agents are analyzing clauses, policies, and risks…</span>
          </div>
          <IntelligenceSkeleton />
        </div>
      )}

      {/* Processing Failed State */}
      {document?.status === "failed" && (
        <EmptyState
          icon={<AlertCircle className="h-6 w-6 text-rose-400" />}
          title="Document Processing Failed"
          description="The AI agent pipeline encountered an error during classification or policy resolution. Please check backend logs or re-upload."
        />
      )}

      {/* Answer Fetch Error State */}
      {isCompleted && answersError && (
        <div className="rounded-xl border border-rose-500/30 bg-rose-500/10 p-4 text-xs text-rose-300 flex items-center gap-2">
          <AlertCircle className="h-4 w-4 shrink-0" />
          <span>Couldn&apos;t load the synthesized intelligence report for this document.</span>
        </div>
      )}

      {/* Empty Findings State */}
      {isCompleted && !answersError && answers !== null && answers.length === 0 && (
        <EmptyState
          icon={<FileSearch className="h-6 w-6 text-white/40" />}
          title="No Intelligence Findings Generated"
          description="The agent run completed without producing any structured answers for this document type."
        />
      )}

      {/* Populated Answers Report */}
      {isCompleted &&
        !answersError &&
        answers !== null &&
        answers.map((answer) => (
          <div key={answer.id} className="flex flex-col gap-4 animate-fadeIn">
            {/* Executive Summary */}
            <div className="rounded-xl border border-white/[0.08] bg-white/[0.02] p-4">
              <h3 className="text-xs font-semibold text-white/60 uppercase tracking-wider mb-2 flex items-center gap-1.5">
                <Sparkles className="h-3.5 w-3.5 text-indigo-400" />
                <span>Executive Summary</span>
              </h3>
              <p className="text-xs leading-relaxed text-white/90">
                {answer.executive_summary || "No executive summary available."}
              </p>
            </div>

            {/* Confidence Score Meter */}
            {answer.confidence_score !== null && (
              <div className="rounded-xl border border-white/[0.08] bg-white/[0.02] p-4">
                <Meter label="Agent Resolution Confidence" value={answer.confidence_score} />
              </div>
            )}

            {/* Risk Flags Grid */}
            {answer.risk_flags.length > 0 && (
              <div className="rounded-xl border border-white/[0.08] bg-white/[0.02] p-4 space-y-2.5">
                <h3 className="text-xs font-semibold text-white/60 uppercase tracking-wider flex items-center gap-1.5">
                  <ShieldAlert className="h-3.5 w-3.5 text-amber-400" />
                  <span>Identified Risk Flags ({answer.risk_flags.length})</span>
                </h3>
                <div className="flex flex-wrap gap-2">
                  {answer.risk_flags.map((flag) => (
                    <RiskBadge key={flag} label={flag} />
                  ))}
                </div>
              </div>
            )}

            {/* Concrete Action Items */}
            {answer.action_items.length > 0 && (
              <div className="rounded-xl border border-white/[0.08] bg-white/[0.02] p-4 space-y-3">
                <h3 className="text-xs font-semibold text-white/60 uppercase tracking-wider flex items-center gap-1.5">
                  <ListTodo className="h-3.5 w-3.5 text-indigo-400" />
                  <span>Recommended Action Items ({answer.action_items.length})</span>
                </h3>
                <ActionItemChecklist items={answer.action_items} />
              </div>
            )}

            {/* Raw Full Response Accordion */}
            {answer.content && <FullResponseDisclosure content={answer.content} />}
          </div>
        ))}
    </Card>
  );
}
