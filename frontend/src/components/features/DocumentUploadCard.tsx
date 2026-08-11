"use client";

import { useState } from "react";

import { Card } from "@/components/ui/Card";
import { Dropzone } from "@/components/features/Dropzone";

export function DocumentUploadCard() {
  const [organizationId, setOrganizationId] = useState("");

  return (
    <Card className="flex w-full max-w-lg flex-col gap-4">
      <h1 className="text-xl font-semibold text-white">Upload Documents</h1>
      <label className="flex flex-col gap-1 text-sm text-white/70">
        Organization ID
        <input
          value={organizationId}
          onChange={(event) => setOrganizationId(event.target.value)}
          placeholder="00000000-0000-0000-0000-000000000000"
          className="rounded-lg border border-white/15 bg-white/5 px-3 py-2 text-sm text-white placeholder:text-white/30 focus:border-indigo-400 focus:outline-none"
        />
      </label>
      <Dropzone organizationId={organizationId} />
    </Card>
  );
}
