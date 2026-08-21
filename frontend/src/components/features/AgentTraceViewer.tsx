"use client";

import { useEffect, useState } from "react";

import { useToast } from "@/contexts/ToastContext";
import { apiClient } from "@/lib/apiClient";
import type { ToolCall } from "@/lib/types";

const POLL_INTERVAL_MS = 1500;
const MAX_POLL_BACKOFF_MS = 15000;

const STEP_LABELS: Record<string, string> = {
  langgraph_supervisor_classify: "Supervisor classified the document",
  mock_classifier: "Deterministic router classified the document",
  search_company_knowledge: "Sales Worker searched company knowledge (ChromaDB)",
  get_internal_pricing_policy: "Sales Worker queried pricing policy (MCP)",
};

function humanizeToolName(toolName: string): string {
  return STEP_LABELS[toolName] ?? toolName.replace(/_/g, " ");
}

function formatJson(value: unknown): string {
  if (value === null || value === undefined) return "—";
  return JSON.stringify(value, null, 2);
}

interface TraceStepProps {
  step: ToolCall;
  index: number;
  isLast: boolean;
}

function TraceStep({ step, index, isLast }: TraceStepProps) {
  const [expanded, setExpanded] = useState(false);

  return (
    <li className="relative flex gap-3 pb-4 last:pb-0">
      {!isLast && (
        <span className="absolute top-2.5 left-[5px] h-full w-px bg-white/10" />
      )}
      <span className="relative z-10 mt-1.5 h-2.5 w-2.5 shrink-0 rounded-full bg-gradient-to-r from-indigo-400 to-violet-400" />
      <div className="flex-1">
        <button
          type="button"
          onClick={() => setExpanded((prev) => !prev)}
          className="flex w-full items-start justify-between gap-2 text-left"
        >
          <span className="text-sm text-white/90">
            <span className="text-white/30">{index + 1}.</span> {humanizeToolName(step.tool_name)}
          </span>
          <svg
            viewBox="0 0 16 16"
            className={`mt-1 h-3 w-3 shrink-0 text-white/40 transition-transform ${expanded ? "rotate-180" : ""}`}
            fill="none"
          >
            <path
              d="M4 6l4 4 4-4"
              stroke="currentColor"
              strokeWidth="1.5"
              strokeLinecap="round"
              strokeLinejoin="round"
            />
          </svg>
        </button>

        {expanded && (
          <div className="mt-2 flex flex-col gap-2 rounded-lg border border-white/10 bg-black/20 p-3 text-xs">
            <div>
              <p className="mb-1 font-medium text-white/40">Input</p>
              <pre className="overflow-x-auto whitespace-pre-wrap text-white/70">
                {formatJson(step.tool_input)}
              </pre>
            </div>
            <div>
              <p className="mb-1 font-medium text-white/40">Output</p>
              <pre className="overflow-x-auto whitespace-pre-wrap text-white/70">
                {formatJson(step.tool_output)}
              </pre>
            </div>
          </div>
        )}
      </div>
    </li>
  );
}

interface AgentTraceViewerProps {
  agentRunId: string | null;
  isTerminal: boolean;
}

export function AgentTraceViewer({ agentRunId, isTerminal }: AgentTraceViewerProps) {
  const [steps, setSteps] = useState<ToolCall[]>([]);
  const [isOpen, setIsOpen] = useState(true);
  const { showError } = useToast();

  useEffect(() => {
    setSteps([]);
    if (!agentRunId) return;

    let cancelled = false;
    let timeoutId: ReturnType<typeof setTimeout>;
    let consecutiveFailures = 0;

    async function poll() {
      try {
        const result = await apiClient.get<ToolCall[]>(
          `/agent-runs/${agentRunId}/tool-calls/`,
        );
        if (cancelled) return;
        setSteps(result);
        consecutiveFailures = 0;
      } catch {
        if (cancelled) return;
        if (consecutiveFailures === 0) {
          showError("Couldn't load the agent's trace log.");
        }
        consecutiveFailures += 1;
      }

      if (!cancelled && !isTerminal) {
        const delay =
          consecutiveFailures > 0
            ? Math.min(POLL_INTERVAL_MS * 2 ** consecutiveFailures, MAX_POLL_BACKOFF_MS)
            : POLL_INTERVAL_MS;
        timeoutId = setTimeout(poll, delay);
      }
    }

    poll();

    return () => {
      cancelled = true;
      clearTimeout(timeoutId);
    };
  }, [agentRunId, isTerminal, showError]);

  if (!agentRunId) return null;

  const isThinking = !isTerminal && steps.length === 0;

  return (
    <div className="rounded-xl border border-white/10 bg-gradient-to-b from-indigo-500/[0.04] to-transparent">
      <button
        type="button"
        onClick={() => setIsOpen((prev) => !prev)}
        className="flex w-full items-center justify-between gap-2 px-4 py-3"
      >
        <span className="flex items-center gap-2 text-sm font-medium text-white/80">
          Agent Thought Process
          {isThinking && (
            <span className="h-1.5 w-1.5 animate-pulse rounded-full bg-status-warning" />
          )}
        </span>
        <svg
          viewBox="0 0 16 16"
          className={`h-3.5 w-3.5 text-white/40 transition-transform ${isOpen ? "rotate-180" : ""}`}
          fill="none"
        >
          <path
            d="M4 6l4 4 4-4"
            stroke="currentColor"
            strokeWidth="1.5"
            strokeLinecap="round"
            strokeLinejoin="round"
          />
        </svg>
      </button>

      {isOpen && (
        <div className="border-t border-white/10 px-4 py-3">
          {isThinking && (
            <p className="text-xs text-white/40">Agent is thinking…</p>
          )}

          {steps.length > 0 && (
            <ul>
              {steps.map((step, index) => (
                <TraceStep
                  key={step.id}
                  step={step}
                  index={index}
                  isLast={index === steps.length - 1}
                />
              ))}
            </ul>
          )}

          {!isThinking && steps.length === 0 && (
            <p className="text-xs text-white/40">No trace steps recorded.</p>
          )}
        </div>
      )}
    </div>
  );
}
