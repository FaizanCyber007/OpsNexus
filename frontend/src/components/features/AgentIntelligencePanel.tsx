"use client";

import { useState } from "react";

import { Card } from "@/components/ui/Card";
import { ActionItemChecklist } from "@/components/ui/ActionItemChecklist";
import { Meter } from "@/components/ui/Meter";
import { RiskBadge } from "@/components/ui/RiskBadge";
import { Shimmer } from "@/components/ui/Shimmer";
import type { Answer, Document } from "@/lib/types";

interface AgentIntelligencePanelProps {
  document: Document | null;
  answers: Answer[] | null;
}

function FullResponseDisclosure({ content }: { content: string }) {
  const [isOpen, setIsOpen] = useState(false);

  return (
    <div className="border-t border-white/10 pt-3">
      <button
        type="button"
        onClick={() => setIsOpen((prev) => !prev)}
        className="text-xs font-medium text-white/50 hover:text-white/80"
      >
        {isOpen ? "Hide full response ▲" : "Show full response ▼"}
      </button>
      {isOpen && (
        <p className="mt-2 whitespace-pre-wrap text-sm leading-relaxed text-white/70">
          {content}
        </p>
      )}
    </div>
  );
}

export function AgentIntelligencePanel({ document, answers }: AgentIntelligencePanelProps) {
  const isPending =
    !document || document.status === "pending" || document.status === "processing";

  return (
    <Card className="flex h-full min-h-[24rem] flex-col gap-4 overflow-y-auto lg:min-h-0">
      <h2 className="text-sm font-medium text-white/70">Agent Intelligence</h2>

      {document?.status === "failed" && (
        <p className="text-sm text-status-critical">Processing failed for this document.</p>
      )}

      {isPending && (
        <div className="flex flex-col gap-3">
          <Shimmer className="h-3.5 w-2/3" />
          <Shimmer className="h-3.5 w-full" />
          <Shimmer className="h-3.5 w-5/6" />
        </div>
      )}

      {document?.status === "completed" && answers === null && (
        <div className="flex flex-col gap-3">
          <Shimmer className="h-3.5 w-2/3" />
          <Shimmer className="h-3.5 w-full" />
        </div>
      )}

      {document?.status === "completed" && answers !== null && answers.length === 0 && (
        <p className="text-sm text-white/50">No answer produced for this document.</p>
      )}

      {document?.status === "completed" &&
        answers !== null &&
        answers.map((answer) => (
          <div key={answer.id} className="flex flex-col gap-4">
            <p className="text-sm leading-relaxed text-white/90">
              {answer.executive_summary || "No executive summary available."}
            </p>

            {answer.confidence_score !== null && (
              <Meter label="Confidence" value={answer.confidence_score} />
            )}

            {answer.risk_flags.length > 0 && (
              <div className="flex flex-col gap-2">
                <h3 className="text-xs font-medium text-white/50">Risk Flags</h3>
                <div className="flex flex-wrap gap-2">
                  {answer.risk_flags.map((flag) => (
                    <RiskBadge key={flag} label={flag} />
                  ))}
                </div>
              </div>
            )}

            {answer.action_items.length > 0 && (
              <div className="flex flex-col gap-2">
                <h3 className="text-xs font-medium text-white/50">Action Items</h3>
                <ActionItemChecklist items={answer.action_items} />
              </div>
            )}

            {answer.content && <FullResponseDisclosure content={answer.content} />}
          </div>
        ))}
    </Card>
  );
}
