"use client";

import { useMemo, useState } from "react";
import {
  Files,
  Activity,
  CheckCircle2,
  Building2,
  Sparkles,
  ShieldCheck,
} from "lucide-react";
import { AnswerDisplay } from "@/components/features/AnswerDisplay";
import { Dropzone } from "@/components/features/Dropzone";
import { RecentRunsTable } from "@/components/features/RecentRunsTable";
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from "@/components/ui/Card";
import { StatTile } from "@/components/ui/StatTile";
import { useTenant, DEMO_ORG_ID } from "@/contexts/TenantContext";
import type { Document } from "@/lib/types";

interface UploadedDoc {
  id: string;
  fileName: string;
}

export function DashboardContent() {
  const { organizationIdDraft, organizationId, handleOrgChange: setTenantDraft } = useTenant();
  const [uploads, setUploads] = useState<UploadedDoc[]>([]);
  const [statuses, setStatuses] = useState<Record<string, Document["status"]>>({});
  const [runsVersion, setRunsVersion] = useState(0);

  const handleOrgChange = (newDraft: string) => {
    setTenantDraft(newDraft);
    setUploads([]);
    setStatuses({});
  };

  const stats = useMemo(() => {
    const values = Object.values(statuses);
    return {
      total: uploads.length,
      processing: values.filter((s) => s === "pending" || s === "processing").length,
      completed: values.filter((s) => s === "completed").length,
    };
  }, [uploads.length, statuses]);

  function handleDeleted(documentId: string) {
    setUploads((prev) => prev.filter((upload) => upload.id !== documentId));
    setStatuses((prev) => {
      const next = { ...prev };
      delete next[documentId];
      return next;
    });
  }

  return (
    <div className="flex w-full max-w-4xl flex-col gap-6">
      {/* Dashboard Top Header */}
      <div className="flex flex-wrap items-center justify-between gap-4 border-b border-white/[0.06] pb-6">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <span className="flex h-2 w-2 rounded-full bg-emerald-400 animate-pulse" />
            <span className="text-[11px] font-mono font-medium text-emerald-400/90 tracking-wide uppercase">
              Autonomous Pipeline Active
            </span>
          </div>
          <h1 className="text-2xl font-bold tracking-tight text-white sm:text-3xl">
            Document Ingestion & Resolution
          </h1>
          <p className="mt-1 text-xs sm:text-sm text-white/50">
            Automated intake, multi-agent reasoning, semantic ChromaDB indexing, and MCP policy lookup.
          </p>
        </div>

        <div className="flex items-center gap-2">
          <div className="flex items-center gap-1.5 rounded-full border border-indigo-500/20 bg-indigo-500/10 px-3 py-1 text-xs text-indigo-300">
            <ShieldCheck className="h-3.5 w-3.5" />
            <span>SOC2 & Enterprise Compliant</span>
          </div>
        </div>
      </div>

      {/* KPI Stats Overview */}
      <div className="grid grid-cols-1 gap-3 sm:grid-cols-3">
        <StatTile
          label="Total Documents Ingested"
          value={stats.total}
          icon={<Files className="h-4 w-4" />}
          subtext="active session"
        />
        <StatTile
          label="Agent Reasoning Active"
          value={stats.processing}
          icon={<Activity className="h-4 w-4 text-amber-400" />}
          accentClass="text-amber-400"
          subtext="in-flight runs"
        />
        <StatTile
          label="Resolved & Verified"
          value={stats.completed}
          icon={<CheckCircle2 className="h-4 w-4 text-emerald-400" />}
          accentClass="text-emerald-400"
          subtext="ready for review"
        />
      </div>

      {/* Organization Selector & Document Intake Card */}
      <Card>
        <CardHeader>
          <div className="flex flex-wrap items-center justify-between gap-2">
            <div className="flex items-center gap-2">
              <div className="flex h-7 w-7 items-center justify-center rounded-lg bg-indigo-500/20 text-indigo-300">
                <Building2 className="h-4 w-4" />
              </div>
              <div>
                <CardTitle>Organization Tenant Scope</CardTitle>
                <CardDescription>
                  Multi-tenant isolation token for ChromaDB collections & document storage.
                </CardDescription>
              </div>
            </div>

            {/* Quick Demo Pill Helper */}
            <button
              type="button"
              onClick={() => handleOrgChange(DEMO_ORG_ID)}
              className="inline-flex items-center gap-1.5 rounded-lg border border-indigo-500/30 bg-indigo-500/10 px-2.5 py-1 text-[11px] font-medium text-indigo-300 hover:bg-indigo-500/20 transition-colors"
            >
              <Sparkles className="h-3 w-3" />
              <span>Use Default Tenant UUID</span>
            </button>
          </div>
        </CardHeader>

        <CardContent className="space-y-5">
          <div>
            <label htmlFor="organization-id-input" className="block text-xs font-medium text-white/70 mb-1.5">
              Organization Identifier (UUIDv4)
            </label>
            <div className="relative">
              <input
                id="organization-id-input"
                value={organizationIdDraft}
                onChange={(event) => handleOrgChange(event.target.value)}
                placeholder="00000000-0000-0000-0000-000000000000"
                className="w-full rounded-xl border border-white/[0.12] bg-white/[0.03] px-4 py-2.5 font-mono text-xs text-white placeholder-white/20 focus:border-indigo-400 focus:bg-white/[0.06] focus:outline-none transition-all shadow-inner"
              />
              {organizationId && (
                <span className="absolute right-3 top-1/2 -translate-y-1/2 flex items-center gap-1 text-[11px] text-emerald-400 font-medium font-sans">
                  <CheckCircle2 className="h-3.5 w-3.5" />
                  Valid Tenant
                </span>
              )}
            </div>
          </div>

          {/* Integrated Dropzone */}
          <Dropzone
            organizationId={organizationId}
            onUploaded={(response, fileName) => {
              setUploads((prev) => [...prev, { id: response.document_id, fileName }]);
              setRunsVersion((prev) => prev + 1);
            }}
          />
        </CardContent>
      </Card>

      {/* Live Pipeline Streaming Results */}
      {uploads.length > 0 && (
        <div className="flex flex-col gap-3">
          <div className="flex items-center justify-between">
            <h2 className="text-sm font-semibold text-white/90">
              Live Resolution Pipeline ({uploads.length})
            </h2>
          </div>
          <div className="space-y-3">
            {uploads.map((upload) => (
              <AnswerDisplay
                key={upload.id}
                documentId={upload.id}
                fileName={upload.fileName}
                onStatusChange={(status) =>
                  setStatuses((prev) => ({ ...prev, [upload.id]: status }))
                }
              />
            ))}
          </div>
        </div>
      )}

      {/* Recent Runs High Density Grid */}
      <RecentRunsTable
        organizationId={organizationId}
        refreshKey={runsVersion}
        onDeleted={handleDeleted}
        onUploadClick={() => window.scrollTo({ top: 0, behavior: "smooth" })}
      />
    </div>
  );
}
