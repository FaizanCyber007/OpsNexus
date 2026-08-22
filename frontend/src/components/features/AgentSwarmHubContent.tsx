"use client";

import { useEffect, useState, useRef } from "react";
import {
  Bot,
  Zap,
  Play,
  CheckCircle2,
  Clock,
  ArrowRight,
  Sparkles,
  ShieldCheck,
  RefreshCw,
  Search,
  Receipt,
  Workflow,
  HelpCircle,
} from "lucide-react";
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from "@/components/ui/Card";
import { StatTile } from "@/components/ui/StatTile";
import { StatusBadge } from "@/components/ui/StatusBadge";
import { useToast } from "@/contexts/ToastContext";
import { useTenant } from "@/contexts/TenantContext";
import { apiClient } from "@/lib/apiClient";
import type { AgentRun, MCPToolInfo } from "@/lib/types";
import { cn } from "@/lib/utils";

const HOW_IT_WORKS_STEPS = [
  {
    step: "01",
    title: "Document Intake",
    description: "Your file is ingested and indexed for fast, accurate search.",
    badge: "Smart Memory",
  },
  {
    step: "02",
    title: "AI Classification",
    description: "The AI identifies whether it is an Invoice, Security Form, or Audit file.",
    badge: "Intent Detection",
  },
  {
    step: "03",
    title: "Policy & Knowledge Lookup",
    description: "Checks against company pricing, vendor terms, and security standards.",
    badge: "Policy Verification",
  },
  {
    step: "04",
    title: "Summary & Risk Report",
    description: "Extracts key takeaways, flags liabilities, and prepares action items.",
    badge: "Verified Output",
  },
];

export function AgentSwarmHubContent() {
  const { organizationId } = useTenant();
  const [mcpTools, setMcpTools] = useState<MCPToolInfo[]>([]);
  const [agentRuns, setAgentRuns] = useState<AgentRun[]>([]);
  const [loading, setLoading] = useState(true);

  // MCP test runner state
  const [activeTool, setActiveTool] = useState<string>("get_internal_pricing_policy");
  const [testQuery, setTestQuery] = useState("pricing tiers and discounts");
  const [testRunning, setTestRunning] = useState(false);
  const [testResult, setTestResult] = useState<any>(null);

  const { showSuccess, showError } = useToast();
  const activeOrgRef = useRef(organizationId);

  useEffect(() => {
    activeOrgRef.current = organizationId;
  }, [organizationId]);

  const loadData = async () => {
    const currentOrg = organizationId;
    try {
      setLoading(true);
      const [mcpData, runsData] = await Promise.all([
        apiClient.getMcpTools(),
        apiClient.getAgentRuns(),
      ]);
      if (activeOrgRef.current === currentOrg) {
        setMcpTools(mcpData.tools);
        setAgentRuns(runsData);
      }
    } catch {
      if (activeOrgRef.current === currentOrg) {
        showError("Failed to load AI system information.");
      }
    } finally {
      if (activeOrgRef.current === currentOrg) {
        setLoading(false);
      }
    }
  };

  useEffect(() => {
    loadData();
  }, [organizationId]);

  const handleTestMcpTool = async () => {
    setTestRunning(true);
    setTestResult(null);
    try {
      const res = await apiClient.testMcpTool({
        tool_name: activeTool,
        params: activeTool === "search_company_knowledge" ? { query: testQuery } : {},
        organization_id: organizationId || undefined,
      });
      setTestResult(res);
      showSuccess("Policy tool executed successfully.");
    } catch {
      showError("Execution failed.");
    } finally {
      setTestRunning(false);
    }
  };

  return (
    <div className="flex w-full max-w-5xl flex-col gap-6">
      {/* Header */}
      <div className="flex flex-wrap items-center justify-between gap-4 border-b border-white/[0.06] pb-6">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <span className="flex h-2 w-2 rounded-full bg-emerald-400 animate-pulse" />
            <span className="text-xs font-medium text-emerald-400">
              AI Models & Knowledge Active
            </span>
          </div>
          <h1 className="text-2xl font-bold tracking-tight text-white sm:text-3xl">
            AI Assistant & Policy Tools
          </h1>
          <p className="mt-1 text-xs sm:text-sm text-white/50">
            How OpsNexus analyzes documents, checks company guidelines, and provides verified answers.
          </p>
        </div>

        <button
          type="button"
          onClick={loadData}
          disabled={loading}
          className="inline-flex items-center gap-2 rounded-xl border border-white/10 bg-white/[0.03] px-3.5 py-2 text-xs font-medium text-white/80 hover:bg-white/[0.08] hover:text-white transition-all disabled:opacity-50"
        >
          <RefreshCw className={cn("h-3.5 w-3.5", loading && "animate-spin text-indigo-400")} />
          <span>Refresh</span>
        </button>
      </div>

      {/* 3 High-Level KPIs */}
      <div className="grid grid-cols-1 gap-3 sm:grid-cols-3">
        <StatTile
          label="AI Model Engine"
          value="Dual-Engine"
          icon={<Bot className="h-4 w-4 text-indigo-400" />}
          subtext="Fast Groq + Gemini Flash"
        />
        <StatTile
          label="Policy Knowledge"
          value="Connected"
          icon={<ShieldCheck className="h-4 w-4 text-emerald-400" />}
          accentClass="text-emerald-400"
          subtext="Internal pricing & guidelines"
        />
        <StatTile
          label="Quality Check"
          value="Automated"
          icon={<CheckCircle2 className="h-4 w-4 text-amber-400" />}
          accentClass="text-amber-400"
          subtext="Self-verifying output"
        />
      </div>

      {/* How It Works - Step Flow */}
      <Card>
        <CardHeader>
          <div className="flex items-center gap-2">
            <div className="flex h-7 w-7 items-center justify-center rounded-lg bg-indigo-500/20 text-indigo-300">
              <Workflow className="h-4 w-4" />
            </div>
            <div>
              <CardTitle>How the AI Assistant Works</CardTitle>
              <CardDescription>
                When you upload a document, OpsNexus follows a 4-step verified workflow.
              </CardDescription>
            </div>
          </div>
        </CardHeader>

        <CardContent>
          <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-4">
            {HOW_IT_WORKS_STEPS.map((step) => (
              <div
                key={step.step}
                className="rounded-xl border border-white/[0.08] bg-white/[0.02] p-4 flex flex-col justify-between space-y-3"
              >
                <div>
                  <div className="flex items-center justify-between text-[11px] text-white/40 mb-2">
                    <span className="font-bold text-indigo-400">Step {step.step}</span>
                    <span className="rounded bg-indigo-500/10 border border-indigo-500/20 px-1.5 py-0.5 text-[10px] text-indigo-300">
                      {step.badge}
                    </span>
                  </div>
                  <h4 className="font-bold text-sm text-white/90 mb-1">{step.title}</h4>
                  <p className="text-xs text-white/60 leading-relaxed">{step.description}</p>
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* Policy & Knowledge Tools Test Section */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <div className="flex h-7 w-7 items-center justify-center rounded-lg bg-emerald-500/20 text-emerald-400">
                <ShieldCheck className="h-4 w-4" />
              </div>
              <div>
                <CardTitle>Company Policy & Guideline Tools</CardTitle>
                <CardDescription>
                  These internal tools allow the AI to look up official company answers and pricing.
                </CardDescription>
              </div>
            </div>
          </div>
        </CardHeader>

        <CardContent className="space-y-4">
          <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
            <div>
              <label className="block text-xs font-medium text-white/70 mb-1.5">
                Select Tool to Test
              </label>
              <select
                value={activeTool}
                onChange={(e) => setActiveTool(e.target.value)}
                className="w-full rounded-xl border border-white/[0.08] bg-white/[0.03] px-3.5 py-2.5 text-xs text-white focus:border-indigo-400 focus:outline-none"
              >
                <option value="get_internal_pricing_policy" className="bg-[#111116]">
                  Company Pricing & Tier Policy
                </option>
                <option value="search_company_knowledge" className="bg-[#111116]">
                  Knowledge Base Search
                </option>
              </select>
            </div>

            {activeTool === "search_company_knowledge" && (
              <div>
                <label className="block text-xs font-medium text-white/70 mb-1.5">
                  Search Question
                </label>
                <input
                  type="text"
                  value={testQuery}
                  onChange={(e) => setTestQuery(e.target.value)}
                  placeholder="e.g. security compliance policies"
                  className="w-full rounded-xl border border-white/[0.08] bg-white/[0.03] px-3.5 py-2.5 text-xs text-white placeholder-white/30 focus:border-indigo-400 focus:outline-none"
                />
              </div>
            )}
          </div>

          <div className="flex items-center justify-between pt-2">
            <button
              type="button"
              onClick={handleTestMcpTool}
              disabled={testRunning}
              className="rounded-xl bg-gradient-to-r from-emerald-600 to-teal-600 px-5 py-2.5 text-xs font-semibold text-white shadow-lg shadow-emerald-500/20 hover:opacity-95 transition-all disabled:opacity-50 flex items-center gap-2"
            >
              {testRunning ? (
                <>
                  <RefreshCw className="h-3.5 w-3.5 animate-spin" />
                  <span>Looking up policy...</span>
                </>
              ) : (
                <>
                  <Play className="h-3.5 w-3.5 fill-white" />
                  <span>Run Policy Check</span>
                </>
              )}
            </button>
          </div>

          {/* Test Result Display */}
          {testResult && (
            <div className="rounded-xl border border-emerald-500/30 bg-emerald-500/5 p-4 space-y-2 mt-3">
              <div className="flex items-center gap-2 text-emerald-400 text-xs font-semibold">
                <CheckCircle2 className="h-4 w-4" />
                <span>Policy Output Retrieved</span>
              </div>
              <div className="rounded-lg bg-black/40 p-3 text-xs text-white/80 leading-relaxed font-sans max-h-60 overflow-y-auto">
                {activeTool === "get_internal_pricing_policy" && testResult.result?.tiers ? (
                  <div className="space-y-2">
                    <p className="font-medium text-white/90">
                      Standard Pricing Tiers ({testResult.result.currency}):
                    </p>
                    <div className="grid grid-cols-1 sm:grid-cols-3 gap-2">
                      {testResult.result.tiers.map((t: any) => (
                        <div key={t.name} className="rounded border border-white/10 bg-white/[0.02] p-2">
                          <span className="font-bold text-indigo-300 block">{t.name}</span>
                          <span className="text-xs text-white/70">${t.price_per_month} / mo</span>
                        </div>
                      ))}
                    </div>
                  </div>
                ) : (
                  <pre className="whitespace-pre-wrap text-[11px] font-mono text-white/70">
                    {JSON.stringify(testResult, null, 2)}
                  </pre>
                )}
              </div>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
