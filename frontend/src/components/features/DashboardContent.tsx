"use client";

import { useMemo, useState } from "react";

import { AnswerDisplay } from "@/components/features/AnswerDisplay";
import { Dropzone } from "@/components/features/Dropzone";
import { Card } from "@/components/ui/Card";
import { StatTile } from "@/components/ui/StatTile";
import type { Document } from "@/lib/types";

interface UploadedDoc {
  id: string;
  fileName: string;
}

export function DashboardContent() {
  const [organizationId, setOrganizationId] = useState("");
  const [uploads, setUploads] = useState<UploadedDoc[]>([]);
  const [statuses, setStatuses] = useState<Record<string, Document["status"]>>({});

  const stats = useMemo(() => {
    const values = Object.values(statuses);
    return {
      total: uploads.length,
      processing: values.filter((s) => s === "pending" || s === "processing").length,
      completed: values.filter((s) => s === "completed").length,
    };
  }, [uploads.length, statuses]);

  return (
    <div className="flex w-full max-w-3xl flex-col gap-6">
      <div>
        <h1 className="text-2xl font-semibold text-white">Document Intake</h1>
        <p className="mt-1 text-sm text-white/50">
          Upload documents to route them through the mock resolution pipeline.
        </p>
      </div>

      <div className="flex gap-4">
        <StatTile label="Total" value={stats.total} />
        <StatTile label="Processing" value={stats.processing} accentClass="text-status-warning" />
        <StatTile label="Completed" value={stats.completed} accentClass="text-status-good" />
      </div>

      <Card className="flex flex-col gap-4">
        <label className="flex flex-col gap-1 text-sm text-white/70">
          Organization ID
          <input
            value={organizationId}
            onChange={(event) => setOrganizationId(event.target.value)}
            placeholder="00000000-0000-0000-0000-000000000000"
            className="rounded-lg border border-white/15 bg-white/5 px-3 py-2 text-sm text-white placeholder:text-white/30 focus:border-indigo-400 focus:outline-none"
          />
        </label>
        <Dropzone
          organizationId={organizationId}
          onUploaded={(response, fileName) =>
            setUploads((prev) => [...prev, { id: response.document_id, fileName }])
          }
        />
      </Card>

      {uploads.length > 0 && (
        <div className="flex flex-col gap-3">
          <h2 className="text-sm font-medium text-white/70">Results</h2>
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
      )}
    </div>
  );
}
