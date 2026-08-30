"use client";

import { useEffect, useState } from "react";
import {
  Terminal,
  ChevronDown,
  ChevronUp,
  Database,
  Route,
  Network,
  Cpu,
  CheckCircle2,
  Copy,
  CheckCheck,
} from "lucide-react";
import { useToast } from "@/contexts/ToastContext";
import { apiClient } from "@/lib/apiClient";
import type { ToolCall } from "@/lib/types";

const POLL_INTERVAL_MS = 1500;
const MAX_POLL_BACKOFF_MS = 15000;
/** Hard ceiling: stop polling after 5 minutes regardless of terminal state. */
const MAX_POLL_DURATION_MS = 5 * 60 * 1000;

const STEP_LABELS: Record<string, { label: string; icon: typeof Database }> = {
  langgraph_supervisor_classify: {
    label: "Supervisor classified the document",
    icon: Route,
  },
  mock_classifier: {
    label: "Deterministic router classified the document",
    icon: Network,
  },
  search_company_knowledge: {
    label: "Sales Worker searched company knowledge (ChromaDB)",
    icon: Database,
  },
  get_internal_pricing_policy: {
    label: "Sales Worker queried pricing policy (MCP Host)",
    icon: Cpu,
  },
};

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
  const [copied, setCopied] = useState(false);

  const meta = STEP_LABELS[step.tool_name] || {
    label: step.tool_name.replace(/_/g, " "),
    icon: Terminal,
  };
  const StepIcon = meta.icon;

  const copyOutput = (e: React.MouseEvent) => {
    e.stopPropagation();
    navigator.clipboard.writeText(formatJson(step.tool_output));
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <li className="relative flex gap-3 pb-3 last:pb-0">
      {/* Animated Connector Line */}
      {!isLast && (
        <span className="absolute top-3 left-[11px] h-full w-px bg-white/10" />
      )}

      {/* Step Icon Badge */}
      <div className="relative z-10 flex h-6 w-6 shrink-0 items-center justify-center rounded-full border border-indigo-500/30 bg-[#121218] text-indigo-300 shadow-sm">
        <StepIcon className="h-3 w-3" />
      </div>

      {/* Step Details */}
      <div className="flex-1 min-w-0">
        <button
          type="button"
          onClick={() => setExpanded((prev) => !prev)}
          className="flex w-full items-center justify-between gap-2 text-left rounded-lg p-1 hover:bg-white/[0.03] transition-colors"
        >
          <div className="flex items-center gap-1.5 truncate">
            <span className="font-mono text-[10px] text-white/30">0{index + 1}.</span>
            <span className="text-xs font-medium text-white/90 truncate">{meta.label}</span>
          </div>

          <div className="flex items-center gap-1 text-white/40 shrink-0">
            <CheckCircle2 className="h-3 w-3 text-emerald-400" />
            {expanded ? (
              <ChevronUp className="h-3.5 w-3.5" />
            ) : (
              <ChevronDown className="h-3.5 w-3.5" />
            )}
          </div>
        </button>

        {expanded && (
          <div className="mt-2 space-y-2 rounded-xl border border-white/[0.08] bg-black/40 p-3 text-[11px]">
            <div className="flex items-center justify-between border-b border-white/5 pb-1 text-white/40">
              <span className="font-mono text-[10px] uppercase tracking-wider">Input Payload</span>
            </div>
            <pre className="overflow-x-auto whitespace-pre-wrap font-mono text-white/70 bg-white/[0.02] p-2 rounded-lg border border-white/[0.03]">
              {formatJson(step.tool_input)}
            </pre>

            <div className="flex items-center justify-between border-b border-white/5 pb-1 pt-1 text-white/40">
              <span className="font-mono text-[10px] uppercase tracking-wider">Execution Output</span>
              <button
                type="button"
                onClick={copyOutput}
                className="flex items-center gap-1 hover:text-white transition-colors"
              >
                {copied ? (
                  <CheckCheck className="h-3 w-3 text-emerald-400" />
                ) : (
                  <Copy className="h-3 w-3" />
                )}
                <span>Copy</span>
              </button>
            </div>
            <pre className="overflow-x-auto whitespace-pre-wrap font-mono text-white/80 bg-white/[0.02] p-2 rounded-lg border border-white/[0.03]">
              {formatJson(step.tool_output)}
            </pre>
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
    if (!agentRunId) return;

    let cancelled = false;
    let timeoutId: ReturnType<typeof setTimeout>;
    let consecutiveFailures = 0;
    const startTime = Date.now();

    async function poll() {
      try {
        const result = await apiClient.get<ToolCall[]>(
          `/agent-runs/${agentRunId}/tool-calls/`
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

      // Stop polling if terminal, max duration exceeded, or too many failures
      if (
        cancelled ||
        isTerminal ||
        Date.now() - startTime >= MAX_POLL_DURATION_MS ||
        consecutiveFailures >= 5
      ) {
        return;
      }

      const delay =
        consecutiveFailures > 0
          ? Math.min(POLL_INTERVAL_MS * 2 ** consecutiveFailures, MAX_POLL_BACKOFF_MS)
          : POLL_INTERVAL_MS;
      timeoutId = setTimeout(poll, delay);
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
    <div className="overflow-hidden rounded-xl border border-white/[0.08] bg-[#121217]/80 backdrop-blur-md">
      <button
        type="button"
        onClick={() => setIsOpen((prev) => !prev)}
        className="flex w-full items-center justify-between gap-2 px-4 py-2.5 hover:bg-white/[0.02] transition-colors"
      >
        <div className="flex items-center gap-2">
          <Terminal className="h-3.5 w-3.5 text-indigo-400" />
          <span className="text-xs font-semibold text-white/90">Agent Workflow Trace</span>
          {isThinking && (
            <span className="flex items-center gap-1 text-[10px] text-amber-300 font-mono">
              <span className="h-1.5 w-1.5 animate-pulse rounded-full bg-amber-400" />
              <span>Synthesizing...</span>
            </span>
          )}
          {steps.length > 0 && (
            <span className="rounded-full bg-white/[0.06] px-1.5 py-0.2 text-[10px] font-mono text-white/50 border border-white/5">
              {steps.length} {steps.length === 1 ? "step" : "steps"}
            </span>
          )}
        </div>

        {isOpen ? (
          <ChevronUp className="h-3.5 w-3.5 text-white/40" />
        ) : (
          <ChevronDown className="h-3.5 w-3.5 text-white/40" />
        )}
      </button>

      {isOpen && (
        <div className="border-t border-white/[0.06] p-3.5">
          {isThinking && (
            <p className="text-xs text-white/40 animate-pulse font-mono">
              Agents executing reasoning loop across tools…
            </p>
          )}

          {steps.length > 0 && (
            <ul className="space-y-1">
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
            <p className="text-xs text-white/40">No tool trace steps recorded for this run.</p>
          )}
        </div>
      )}
    </div>
  );
}
