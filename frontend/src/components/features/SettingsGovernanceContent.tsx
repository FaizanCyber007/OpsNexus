"use client";

import { useEffect, useState, useRef } from "react";
import { motion } from "framer-motion";
import {
  Building2,
  BellRing,
  BookOpen,
  Activity,
  Plus,
  Trash2,
  ToggleLeft,
  ToggleRight,
  ShieldCheck,
  CheckCircle2,
  RefreshCw,
  Sparkles,
} from "lucide-react";
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from "@/components/ui/Card";
import { StatTile } from "@/components/ui/StatTile";
import { EmptyState } from "@/components/ui/EmptyState";
import { useToast } from "@/contexts/ToastContext";
import { useTenant, DEMO_ORG_ID } from "@/contexts/TenantContext";
import { apiClient } from "@/lib/apiClient";
import type { HealthRule, Playbook, SystemStatus } from "@/lib/types";
import { cn } from "@/lib/utils";
import { Modal } from "@/components/ui/Modal";

export function SettingsGovernanceContent() {
  const { organizationIdDraft, organizationId, handleOrgChange, resetTenant } = useTenant();
  const [activeTab, setActiveTab] = useState<"workspace" | "alerts" | "guides" | "status">("workspace");

  // Data states
  const [healthRules, setHealthRules] = useState<HealthRule[]>([]);
  const [playbooks, setPlaybooks] = useState<Playbook[]>([]);
  const [systemStatus, setSystemStatus] = useState<SystemStatus | null>(null);
  const [loading, setLoading] = useState(true);

  // Alert Rule Modal / Form
  const [showRuleModal, setShowRuleModal] = useState(false);
  const [ruleName, setRuleName] = useState("");
  const [ruleMetric, setRuleMetric] = useState("cpu_usage");
  const [ruleThreshold, setRuleThreshold] = useState("80");
  const [ruleDesc, setRuleDesc] = useState("");

  // Playbook Modal / Form
  const [showPlaybookModal, setShowPlaybookModal] = useState(false);
  const [playbookName, setPlaybookName] = useState("");
  const [playbookDesc, setPlaybookDesc] = useState("");
  const [playbookContent, setPlaybookContent] = useState("");

  const { showSuccess, showError } = useToast();

  const activeOrgRef = useRef(organizationId);
  useEffect(() => {
    activeOrgRef.current = organizationId;
  }, [organizationId]);

  const loadAll = async () => {
    const currentOrg = organizationId;
    try {
      setLoading(true);
      const [rules, pb, sys] = await Promise.all([
        apiClient.getHealthRules(currentOrg || undefined).catch(() => []),
        apiClient.getPlaybooks(currentOrg || undefined).catch(() => []),
        apiClient.getSystemStatus().catch(() => null),
      ]);
      if (activeOrgRef.current === currentOrg) {
        setHealthRules(rules);
        setPlaybooks(pb);
        setSystemStatus(sys);
      }
    } catch {
      if (activeOrgRef.current === currentOrg) {
        showError("Failed to fetch settings.");
      }
    } finally {
      if (activeOrgRef.current === currentOrg) {
        setLoading(false);
      }
    }
  };

  useEffect(() => {
    loadAll();
  }, [organizationId]);

  // Alert Rule Handlers
  const handleCreateRule = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!ruleName.trim()) {
      showError("Rule name is required.");
      return;
    }
    try {
      const parsedThreshold = parseFloat(ruleThreshold);
      if (!Number.isFinite(parsedThreshold)) {
        showError("Invalid threshold value.");
        return;
      }

      const created = await apiClient.createHealthRule({
        organization: organizationId || DEMO_ORG_ID,
        name: ruleName,
        metric: ruleMetric,
        threshold: parsedThreshold,
        description: ruleDesc,
        is_active: true,
      });
      setHealthRules((prev) => [created, ...prev]);
      setShowRuleModal(false);
      setRuleName("");
      setRuleDesc("");
      showSuccess(`Alert Rule '${created.name}' created.`);
    } catch {
      showError("Failed to create alert rule.");
    }
  };

  const handleToggleRule = async (rule: HealthRule) => {
    try {
      const updated = await apiClient.updateHealthRule(rule.id, { is_active: !rule.is_active });
      setHealthRules((prev) => prev.map((r) => (r.id === rule.id ? updated : r)));
      showSuccess(`Alert rule ${updated.is_active ? "enabled" : "disabled"}.`);
    } catch {
      showError("Failed to update rule.");
    }
  };

  const handleDeleteRule = async (id: string) => {
    if (!confirm("Are you sure you want to delete this alert rule?")) return;
    try {
      await apiClient.deleteHealthRule(id);
      setHealthRules((prev) => prev.filter((r) => r.id !== id));
      showSuccess("Alert Rule deleted.");
    } catch {
      showError("Failed to delete rule.");
    }
  };

  // Playbook Handlers
  const handleCreatePlaybook = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!playbookName.trim()) {
      showError("Guide title is required.");
      return;
    }
    try {
      const created = await apiClient.createPlaybook({
        organization: organizationId || DEMO_ORG_ID,
        name: playbookName,
        description: playbookDesc,
        content: playbookContent,
        is_active: true,
      });
      setPlaybooks((prev) => [created, ...prev]);
      setShowPlaybookModal(false);
      setPlaybookName("");
      setPlaybookDesc("");
      setPlaybookContent("");
      showSuccess(`Operating Guide '${created.name}' created.`);
    } catch {
      showError("Failed to create guide.");
    }
  };

  const handleTogglePlaybook = async (pb: Playbook) => {
    try {
      const updated = await apiClient.updatePlaybook(pb.id, { is_active: !pb.is_active });
      setPlaybooks((prev) => prev.map((p) => (p.id === pb.id ? updated : p)));
      showSuccess(`Guide ${updated.is_active ? "enabled" : "archived"}.`);
    } catch {
      showError("Failed to update guide.");
    }
  };

  const handleDeletePlaybook = async (id: string) => {
    if (!confirm("Are you sure you want to delete this guide?")) return;
    try {
      await apiClient.deletePlaybook(id);
      setPlaybooks((prev) => prev.filter((p) => p.id !== id));
      showSuccess("Operating Guide deleted.");
    } catch {
      showError("Failed to delete guide.");
    }
  };

  return (
    <div className="flex w-full max-w-5xl flex-col gap-6">
      {/* Header */}
      <div className="flex flex-wrap items-center justify-between gap-4 border-b border-white/[0.06] pb-6">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-white sm:text-3xl">
            Rules & Settings
          </h1>
          <p className="mt-1 text-xs sm:text-sm text-white/50">
            Configure automatic alert triggers, standard operating procedures, and company workspace options.
          </p>
        </div>

        <button
          type="button"
          onClick={loadAll}
          disabled={loading}
          className="inline-flex items-center gap-2 rounded-xl border border-white/10 bg-white/[0.03] px-3.5 py-2 text-xs font-medium text-white/80 hover:bg-white/[0.08] hover:text-white transition-all disabled:opacity-50"
        >
          <RefreshCw className={cn("h-3.5 w-3.5", loading && "animate-spin text-indigo-400")} />
          <span>Refresh</span>
        </button>
      </div>

      {/* Tabs Navigation */}
      <div className="flex items-center gap-1 rounded-2xl border border-white/[0.08] bg-[#111116]/90 p-1.5 backdrop-blur-xl">
        {[
          { id: "workspace", label: "Workspace & Company", icon: Building2 },
          { id: "alerts", label: `Alert Rules (${healthRules.length})`, icon: BellRing },
          { id: "guides", label: `Operating Guides (${playbooks.length})`, icon: BookOpen },
          { id: "status", label: "System Health", icon: Activity },
        ].map((tab) => {
          const Icon = tab.icon;
          const isActive = activeTab === tab.id;
          return (
            <button
              key={tab.id}
              type="button"
              onClick={() => setActiveTab(tab.id as any)}
              className={cn(
                "relative flex flex-1 items-center justify-center gap-2 rounded-xl py-2.5 text-xs font-semibold transition-colors",
                isActive ? "text-white" : "text-white/50 hover:text-white/80"
              )}
            >
              {isActive && (
                <motion.div
                  layoutId="settingsTabIndicator"
                  className="absolute inset-0 rounded-xl bg-gradient-to-r from-indigo-500/25 to-violet-500/25 border border-indigo-500/30 shadow-inner"
                  transition={{ type: "spring", stiffness: 400, damping: 30 }}
                />
              )}
              <span className="relative z-10 flex items-center gap-1.5">
                <Icon className={cn("h-4 w-4", isActive ? "text-indigo-400" : "text-white/40")} />
                <span>{tab.label}</span>
              </span>
            </button>
          );
        })}
      </div>

      {/* Tab 1: Workspace & Company */}
      {activeTab === "workspace" && (
        <div className="space-y-6">
          <Card>
            <CardHeader>
              <div className="flex items-center justify-between">
                <div>
                  <CardTitle>Workspace Configuration</CardTitle>
                  <CardDescription>
                    Your files, summaries, and activity records are securely isolated to this workspace.
                  </CardDescription>
                </div>

                <button
                  type="button"
                  onClick={resetTenant}
                  className="inline-flex items-center gap-1.5 rounded-lg border border-indigo-500/30 bg-indigo-500/10 px-3 py-1.5 text-xs font-medium text-indigo-300 hover:bg-indigo-500/20 transition-colors"
                >
                  <Sparkles className="h-3 w-3" />
                  <span>Reset to Default Workspace</span>
                </button>
              </div>
            </CardHeader>

            <CardContent className="space-y-4">
              <div>
                <label className="block text-xs font-medium text-white/70 mb-1.5">
                  Workspace Identifier
                </label>
                <div className="relative">
                  <input
                    value={organizationIdDraft}
                    onChange={(e) => handleOrgChange(e.target.value)}
                    placeholder="Enter workspace ID..."
                    className="w-full rounded-xl border border-white/[0.12] bg-white/[0.03] px-4 py-2.5 font-mono text-xs text-white placeholder-white/20 focus:border-indigo-400 focus:outline-none transition-all shadow-inner"
                  />
                  {organizationId && (
                    <span className="absolute right-3 top-1/2 -translate-y-1/2 flex items-center gap-1 text-xs text-emerald-400 font-medium font-sans">
                      <CheckCircle2 className="h-3.5 w-3.5" />
                      Active
                    </span>
                  )}
                </div>
              </div>

              <div className="rounded-xl border border-white/[0.06] bg-black/30 p-4 text-xs space-y-1.5 text-white/70">
                <div className="flex items-center gap-2 text-white font-semibold">
                  <ShieldCheck className="h-4 w-4 text-emerald-400" />
                  <span>Enterprise Privacy Protection</span>
                </div>
                <p>
                  Documents uploaded to this workspace are encrypted and never shared with other organizations or used for public AI training.
                </p>
              </div>
            </CardContent>
          </Card>
        </div>
      )}

      {/* Tab 2: Alert Rules */}
      {activeTab === "alerts" && (
        <div className="space-y-6">
          <div className="flex items-center justify-between">
            <div>
              <h3 className="text-base font-bold text-white">Automated Alert Rules</h3>
              <p className="text-xs text-white/50">
                Receive alerts when document processing takes longer than expected or error thresholds are met.
              </p>
            </div>

            <button
              type="button"
              onClick={() => setShowRuleModal(true)}
              className="inline-flex items-center gap-1.5 rounded-xl bg-indigo-600 px-4 py-2 text-xs font-semibold text-white hover:bg-indigo-500 transition-all shadow-lg shadow-indigo-500/25"
            >
              <Plus className="h-3.5 w-3.5" />
              <span>Create Alert Rule</span>
            </button>
          </div>

          {healthRules.length === 0 ? (
            <EmptyState
              icon={<BellRing className="h-8 w-8 text-white/30" />}
              title="No alert rules created yet"
              description="Create alert rules to monitor system responsiveness and processing times."
              actionLabel="Create Alert Rule"
              onAction={() => setShowRuleModal(true)}
            />
          ) : (
            <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
              {healthRules.map((rule) => (
                <Card key={rule.id} className="p-5 flex flex-col justify-between space-y-4">
                  <div className="space-y-2">
                    <div className="flex items-center justify-between">
                      <span className="text-[11px] font-semibold text-indigo-300 bg-indigo-500/10 border border-indigo-500/20 px-2 py-0.5 rounded-md">
                        {rule.metric === "cpu_usage"
                          ? "Processing Load"
                          : rule.metric === "latency_p99"
                          ? "Response Time"
                          : "Error Threshold"}
                      </span>
                      <button
                        type="button"
                        onClick={() => handleToggleRule(rule)}
                        className="text-white/60 hover:text-white transition-colors"
                      >
                        {rule.is_active ? (
                          <span className="flex items-center gap-1 text-xs text-emerald-400 font-medium">
                            <ToggleRight className="h-5 w-5" /> Enabled
                          </span>
                        ) : (
                          <span className="flex items-center gap-1 text-xs text-white/40 font-medium">
                            <ToggleLeft className="h-5 w-5" /> Disabled
                          </span>
                        )}
                      </button>
                    </div>

                    <h4 className="font-bold text-sm text-white/90">{rule.name}</h4>
                    <p className="text-xs text-white/60 line-clamp-2">{rule.description || "Monitors threshold anomalies."}</p>

                    <div className="pt-2 border-t border-white/[0.04] flex items-center justify-between text-xs">
                      <span className="text-white/40">Threshold:</span>
                      <span className="font-semibold text-amber-400">
                        {rule.threshold}{rule.metric === "latency_p99" ? "ms" : "%"}
                      </span>
                    </div>
                  </div>

                  <div className="flex items-center justify-end pt-2 border-t border-white/[0.06]">
                    <button
                      type="button"
                      onClick={() => handleDeleteRule(rule.id)}
                      className="text-rose-400 hover:text-rose-300 transition-colors p-1"
                      title="Delete"
                    >
                      <Trash2 className="h-4 w-4" />
                    </button>
                  </div>
                </Card>
              ))}
            </div>
          )}
        </div>
      )}

      {/* Tab 3: Operating Guides (Playbooks) */}
      {activeTab === "guides" && (
        <div className="space-y-6">
          <div className="flex items-center justify-between">
            <div>
              <h3 className="text-base font-bold text-white">Standard Operating Guides</h3>
              <p className="text-xs text-white/50">
                Actionable guidelines for your team when reviewing contracts, compliance red flags, or billing issues.
              </p>
            </div>

            <button
              type="button"
              onClick={() => setShowPlaybookModal(true)}
              className="inline-flex items-center gap-1.5 rounded-xl bg-indigo-600 px-4 py-2 text-xs font-semibold text-white hover:bg-indigo-500 transition-all shadow-lg shadow-indigo-500/25"
            >
              <Plus className="h-3.5 w-3.5" />
              <span>Create New Guide</span>
            </button>
          </div>

          {playbooks.length === 0 ? (
            <EmptyState
              icon={<BookOpen className="h-8 w-8 text-white/30" />}
              title="No operating guides created yet"
              description="Create guides to document standard procedures for contract reviews and vendor escalations."
              actionLabel="Create New Guide"
              onAction={() => setShowPlaybookModal(true)}
            />
          ) : (
            <div className="space-y-4">
              {playbooks.map((pb) => (
                <Card key={pb.id} className="p-5 space-y-3">
                  <div className="flex items-start justify-between gap-4">
                    <div>
                      <div className="flex items-center gap-2 mb-1">
                        <h4 className="font-bold text-sm text-white/90">{pb.name}</h4>
                        <span
                          className={cn(
                            "rounded px-2 py-0.5 text-[10px] font-semibold",
                            pb.is_active
                              ? "bg-emerald-500/20 text-emerald-300 border border-emerald-500/30"
                              : "bg-white/10 text-white/40"
                          )}
                        >
                          {pb.is_active ? "Active" : "Archived"}
                        </span>
                      </div>
                      <p className="text-xs text-white/60">{pb.description}</p>
                    </div>

                    <div className="flex items-center gap-2">
                      <button
                        type="button"
                        onClick={() => handleTogglePlaybook(pb)}
                        className="rounded-lg border border-white/10 bg-white/[0.02] px-2.5 py-1 text-xs font-medium text-white/70 hover:bg-white/[0.05]"
                      >
                        {pb.is_active ? "Archive" : "Activate"}
                      </button>
                      <button
                        type="button"
                        onClick={() => handleDeletePlaybook(pb.id)}
                        className="rounded-lg border border-rose-500/20 p-1.5 text-rose-400 hover:bg-rose-500/10"
                        title="Delete"
                      >
                        <Trash2 className="h-3.5 w-3.5" />
                      </button>
                    </div>
                  </div>

                  {pb.content && (
                    <div className="rounded-xl bg-black/40 p-4 border border-white/[0.06] text-xs text-white/80 whitespace-pre-wrap leading-relaxed">
                      {pb.content}
                    </div>
                  )}
                </Card>
              ))}
            </div>
          )}
        </div>
      )}

      {/* Tab 4: System Health */}
      {activeTab === "status" && (
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
          <Card className="p-5 space-y-3">
            <div className="flex items-center justify-between">
              <span className="text-xs text-white font-semibold">AI Assistant</span>
              <span className={cn("rounded-full border px-2.5 py-0.5 text-xs font-medium", systemStatus ? "bg-emerald-500/20 border-emerald-500/30 text-emerald-400" : "bg-white/10 border-white/20 text-white/50")}>
                {systemStatus ? "Operational" : "Unknown"}
              </span>
            </div>
            <h4 className="font-bold text-sm text-white">Dual AI Model Pipeline</h4>
            <p className="text-xs text-white/60">
              High-speed reasoning for quick answers and deep verification for complex documents.
            </p>
          </Card>

          <Card className="p-5 space-y-3">
            <div className="flex items-center justify-between">
              <span className="text-xs text-white font-semibold">Search & Memory</span>
              <span className={cn("rounded-full border px-2.5 py-0.5 text-xs font-medium", systemStatus ? "bg-emerald-500/20 border-emerald-500/30 text-emerald-400" : "bg-white/10 border-white/20 text-white/50")}>
                {systemStatus ? "Operational" : "Unknown"}
              </span>
            </div>
            <h4 className="font-bold text-sm text-white">Document Search Engine</h4>
            <p className="text-xs text-white/60">
              Indexes document sections for sub-second clause lookup and accurate source citations.
            </p>
          </Card>

          <Card className="p-5 space-y-3">
            <div className="flex items-center justify-between">
              <span className="text-xs text-white font-semibold">Data Protection</span>
              <span className={cn("rounded-full border px-2.5 py-0.5 text-xs font-medium", systemStatus ? "bg-emerald-500/20 border-emerald-500/30 text-emerald-400" : "bg-white/10 border-white/20 text-white/50")}>
                {systemStatus ? "Protected" : "Unknown"}
              </span>
            </div>
            <h4 className="font-bold text-sm text-white">Encrypted Workspace Storage</h4>
            <p className="text-xs text-white/60">
              Enterprise security headers, automated audit trail, and rate limiting active.
            </p>
          </Card>
        </div>
      )}

      {/* Add Health Rule Modal */}
      <Modal isOpen={showRuleModal} onClose={() => setShowRuleModal(false)} title="Create Alert Rule" className="max-w-md p-6">
          <form
            onSubmit={handleCreateRule}
            className="space-y-4"
          >
            <div className="flex items-center justify-between border-b border-white/[0.08] pb-3">
              <h3 className="font-bold text-base text-white">Create Alert Rule</h3>
              <button
                type="button"
                onClick={() => setShowRuleModal(false)}
                className="text-white/40 hover:text-white"
              >
                ✕
              </button>
            </div>

            <div className="space-y-3 text-xs">
              <div>
                <label className="block text-white/70 font-medium mb-1">Rule Name</label>
                <input
                  type="text"
                  value={ruleName}
                  onChange={(e) => setRuleName(e.target.value)}
                  placeholder="e.g. Processing Delay Alert"
                  className="w-full rounded-xl border border-white/[0.08] bg-white/[0.03] px-3 py-2 text-white focus:border-indigo-400 focus:outline-none"
                  required
                />
              </div>

              <div>
                <label className="block text-white/70 font-medium mb-1">Condition</label>
                <select
                  value={ruleMetric}
                  onChange={(e) => setRuleMetric(e.target.value)}
                  className="w-full rounded-xl border border-white/[0.08] bg-white/[0.03] px-3 py-2 text-white focus:border-indigo-400 focus:outline-none"
                >
                  <option value="cpu_usage" className="bg-[#111116]">System Processing Load (%)</option>
                  <option value="latency_p99" className="bg-[#111116]">Response Time (ms)</option>
                  <option value="error_rate" className="bg-[#111116]">Error Rate (%)</option>
                </select>
              </div>

              <div>
                <label className="block text-white/70 font-medium mb-1">Threshold Value</label>
                <input
                  type="number"
                  value={ruleThreshold}
                  onChange={(e) => setRuleThreshold(e.target.value)}
                  className="w-full rounded-xl border border-white/[0.08] bg-white/[0.03] px-3 py-2 text-white focus:border-indigo-400 focus:outline-none"
                  required
                />
              </div>

              <div>
                <label className="block text-white/70 font-medium mb-1">Notes (Optional)</label>
                <textarea
                  value={ruleDesc}
                  onChange={(e) => setRuleDesc(e.target.value)}
                  rows={2}
                  placeholder="What action should be taken..."
                  className="w-full rounded-xl border border-white/[0.08] bg-white/[0.03] px-3 py-2 text-white focus:border-indigo-400 focus:outline-none"
                />
              </div>
            </div>

            <div className="flex items-center justify-end gap-2 pt-3 border-t border-white/[0.08]">
              <button
                type="button"
                onClick={() => setShowRuleModal(false)}
                className="rounded-xl border border-white/10 px-3.5 py-2 text-xs font-medium text-white/70 hover:bg-white/[0.05]"
              >
                Cancel
              </button>
              <button
                type="submit"
                className="rounded-xl bg-indigo-600 px-4 py-2 text-xs font-semibold text-white hover:bg-indigo-500 shadow-lg shadow-indigo-500/25"
              >
                Save Rule
              </button>
            </div>
          </form>
      </Modal>

      {/* Add Playbook Modal */}
      <Modal isOpen={showPlaybookModal} onClose={() => setShowPlaybookModal(false)} title="Create Operating Guide" className="max-w-lg p-6">
          <form
            onSubmit={handleCreatePlaybook}
            className="space-y-4"
          >
            <div className="flex items-center justify-between border-b border-white/[0.08] pb-3">
              <h3 className="font-bold text-base text-white">Create Operating Guide</h3>
              <button
                type="button"
                onClick={() => setShowPlaybookModal(false)}
                className="text-white/40 hover:text-white"
              >
                ✕
              </button>
            </div>

            <div className="space-y-3 text-xs">
              <div>
                <label className="block text-white/70 font-medium mb-1">Guide Title</label>
                <input
                  type="text"
                  value={playbookName}
                  onChange={(e) => setPlaybookName(e.target.value)}
                  placeholder="e.g. Vendor Risk Review Guide"
                  className="w-full rounded-xl border border-white/[0.08] bg-white/[0.03] px-3 py-2 text-white focus:border-indigo-400 focus:outline-none"
                  required
                />
              </div>

              <div>
                <label className="block text-white/70 font-medium mb-1">Summary</label>
                <input
                  type="text"
                  value={playbookDesc}
                  onChange={(e) => setPlaybookDesc(e.target.value)}
                  placeholder="When to use this guide..."
                  className="w-full rounded-xl border border-white/[0.08] bg-white/[0.03] px-3 py-2 text-white focus:border-indigo-400 focus:outline-none"
                />
              </div>

              <div>
                <label className="block text-white/70 font-medium mb-1">Step-by-Step Instructions</label>
                <textarea
                  value={playbookContent}
                  onChange={(e) => setPlaybookContent(e.target.value)}
                  rows={5}
                  placeholder="1. Check payment terms against pricing policy.&#10;2. Verify security certifications.&#10;3. Obtain manager approval for discounts over 10%."
                  className="w-full rounded-xl border border-white/[0.08] bg-white/[0.03] px-3 py-2 text-xs text-white focus:border-indigo-400 focus:outline-none"
                />
              </div>
            </div>

            <div className="flex items-center justify-end gap-2 pt-3 border-t border-white/[0.08]">
              <button
                type="button"
                onClick={() => setShowPlaybookModal(false)}
                className="rounded-xl border border-white/10 px-3.5 py-2 text-xs font-medium text-white/70 hover:bg-white/[0.05]"
              >
                Cancel
              </button>
              <button
                type="submit"
                className="rounded-xl bg-indigo-600 px-4 py-2 text-xs font-semibold text-white hover:bg-indigo-500 shadow-lg shadow-indigo-500/25"
              >
                Save Guide
              </button>
            </div>
          </form>
      </Modal>
    </div>
  );
}
