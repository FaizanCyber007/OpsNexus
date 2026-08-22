"use client";

import { useMemo, useState } from "react";
import Link from "next/link";
import {
  FileText,
  Clock,
  CheckCircle2,
  Sparkles,
  ArrowRight,
  ShieldCheck,
  Receipt,
  FileSpreadsheet,
  FolderOpen,
} from "lucide-react";
import { AnswerDisplay } from "@/components/features/AnswerDisplay";
import { Dropzone } from "@/components/features/Dropzone";
import { RecentRunsTable } from "@/components/features/RecentRunsTable";
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from "@/components/ui/Card";
import { StatTile } from "@/components/ui/StatTile";
import { useTenant } from "@/contexts/TenantContext";
import type { Document } from "@/lib/types";

interface UploadedDoc {
  id: string;
  fileName: string;
}

export function DashboardContent() {
  const { organizationId } = useTenant();
  const [uploads, setUploads] = useState<UploadedDoc[]>([]);
  const [statuses, setStatuses] = useState<Record<string, Document["status"]>>({});
  const [runsVersion, setRunsVersion] = useState(0);

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
    <div className="flex w-full max-w-5xl flex-col gap-6">
      {/* Friendly Dashboard Header */}
      <div className="flex flex-wrap items-center justify-between gap-4 border-b border-white/[0.06] pb-6">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <span className="flex h-2 w-2 rounded-full bg-emerald-400 animate-pulse" />
            <span className="text-xs font-medium text-emerald-400">
              AI Document Assistant Active
            </span>
          </div>
          <h1 className="text-2xl font-bold tracking-tight text-white sm:text-3xl">
            Document Operations & Intake
          </h1>
          <p className="mt-1 text-xs sm:text-sm text-white/60">
            Upload vendor questionnaires, invoices, or compliance documents for automated review, risk flags, and answers.
          </p>
        </div>

        <div className="flex items-center gap-2">
          <Link
            href="/dashboard/documents"
            className="inline-flex items-center gap-2 rounded-xl border border-white/10 bg-white/[0.04] px-4 py-2 text-xs font-semibold text-white hover:bg-white/[0.08] transition-colors"
          >
            <FolderOpen className="h-3.5 w-3.5" />
            <span>View All Documents</span>
          </Link>
        </div>
      </div>

      {/* 3 Simple, Clear KPI Cards */}
      <div className="grid grid-cols-1 gap-3 sm:grid-cols-3">
        <StatTile
          label="Documents Ingested"
          value={stats.total}
          icon={<FileText className="h-4 w-4 text-indigo-400" />}
          subtext="in this session"
        />
        <StatTile
          label="Currently Analyzing"
          value={stats.processing}
          icon={<Clock className="h-4 w-4 text-amber-400" />}
          accentClass="text-amber-400"
          subtext="AI reviewing clauses"
        />
        <StatTile
          label="Ready & Verified"
          value={stats.completed}
          icon={<CheckCircle2 className="h-4 w-4 text-emerald-400" />}
          accentClass="text-emerald-400"
          subtext="ready for questions"
        />
      </div>

      {/* Clean Document Upload Card */}
      <Card className="border-indigo-500/20 bg-gradient-to-b from-white/[0.03] to-transparent">
        <CardHeader className="pb-3">
          <div className="flex items-center gap-2">
            <div className="flex h-7 w-7 items-center justify-center rounded-lg bg-indigo-500/20 text-indigo-300">
              <Sparkles className="h-4 w-4" />
            </div>
            <div>
              <CardTitle>Upload a New Document</CardTitle>
              <CardDescription>
                Drag and drop your file below. Supported: PDF, Word (.docx), Excel/CSV, Text, and Logs.
              </CardDescription>
            </div>
          </div>
        </CardHeader>

        <CardContent className="pt-2">
          <Dropzone
            organizationId={organizationId}
            onUploaded={(response, fileName) => {
              setUploads((prev) => [...prev, { id: response.document_id, fileName }]);
              setRunsVersion((prev) => prev + 1);
            }}
          />
        </CardContent>
      </Card>

      {/* Live AI Analysis Results (When Uploaded) */}
      {uploads.length > 0 && (
        <div className="flex flex-col gap-3">
          <div className="flex items-center justify-between">
            <h2 className="text-sm font-semibold text-white/90">
              Recent Ingestion Results ({uploads.length})
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

      {/* Recent Ingested Documents List */}
      <RecentRunsTable
        organizationId={organizationId}
        refreshKey={runsVersion}
        onDeleted={handleDeleted}
        onUploadClick={() => window.scrollTo({ top: 0, behavior: "smooth" })}
      />
    </div>
  );
}
