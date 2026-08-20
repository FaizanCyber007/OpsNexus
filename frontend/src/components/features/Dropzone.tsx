"use client";

import { useRef, useState, type DragEvent } from "react";

import { LoadingSpinner } from "@/components/ui/LoadingSpinner";
import { StatusBadge } from "@/components/ui/StatusBadge";
import { apiClient, ApiError } from "@/lib/apiClient";
import type { Document, DocumentUploadResponse } from "@/lib/types";

interface DropzoneProps {
  organizationId: string;
  docType?: Document["doc_type"];
  onUploaded?: (response: DocumentUploadResponse, fileName: string) => void;
}

interface UploadItem {
  id: string;
  name: string;
  status: "uploading" | "done" | "error";
  message?: string;
}

export function Dropzone({ organizationId, docType = "other", onUploaded }: DropzoneProps) {
  const [isDragging, setIsDragging] = useState(false);
  const [uploads, setUploads] = useState<UploadItem[]>([]);
  const inputRef = useRef<HTMLInputElement>(null);

  async function uploadFile(file: File) {
    const id = `${file.name}-${Date.now()}`;
    setUploads((prev) => [...prev, { id, name: file.name, status: "uploading" }]);

    try {
      const response = await apiClient.post<DocumentUploadResponse>("/documents/", {
        organization: organizationId,
        doc_type: docType,
        file_path: file.name,
      });
      setUploads((prev) =>
        prev.map((item) => (item.id === id ? { ...item, status: "done" } : item)),
      );
      onUploaded?.(response, file.name);
    } catch (error) {
      const message =
        error instanceof ApiError ? `Upload failed (${error.status})` : "Upload failed";
      setUploads((prev) =>
        prev.map((item) => (item.id === id ? { ...item, status: "error", message } : item)),
      );
    }
  }

  function handleFiles(files: FileList | null) {
    if (!files || !organizationId) return;
    Array.from(files).forEach(uploadFile);
  }

  function handleDrop(event: DragEvent<HTMLDivElement>) {
    event.preventDefault();
    setIsDragging(false);
    handleFiles(event.dataTransfer.files);
  }

  const disabled = !organizationId;

  return (
    <div className="flex flex-col gap-4">
      <div
        onDragOver={(event) => {
          event.preventDefault();
          if (!disabled) setIsDragging(true);
        }}
        onDragLeave={() => setIsDragging(false)}
        onDrop={handleDrop}
        onClick={() => !disabled && inputRef.current?.click()}
        className={`flex flex-col items-center justify-center gap-3 rounded-xl border-2 border-dashed px-6 py-12 text-center transition-colors ${
          disabled
            ? "cursor-not-allowed border-white/10 bg-white/[0.02] opacity-60"
            : isDragging
              ? "cursor-pointer border-indigo-400 bg-indigo-400/10"
              : "cursor-pointer border-white/20 bg-white/5 hover:border-indigo-400/50 hover:bg-white/[0.07]"
        }`}
      >
        <svg
          viewBox="0 0 24 24"
          className={`h-9 w-9 ${isDragging ? "text-indigo-300" : "text-white/40"}`}
          fill="none"
          stroke="currentColor"
        >
          <path
            d="M12 16V4m0 0 4 4m-4-4-4 4M5 16v2.5A1.5 1.5 0 0 0 6.5 20h11a1.5 1.5 0 0 0 1.5-1.5V16"
            strokeWidth="1.5"
            strokeLinecap="round"
            strokeLinejoin="round"
          />
        </svg>
        <div>
          <p className="text-sm font-medium text-white/90">
            Drag and drop files here, or click to browse
          </p>
          <p className="mt-1 text-xs text-white/40">
            {disabled
              ? "Enter an Organization ID above to enable uploads"
              : "Any file type — routed automatically by name and extension"}
          </p>
        </div>
        <input
          ref={inputRef}
          type="file"
          multiple
          disabled={disabled}
          className="hidden"
          onChange={(event) => handleFiles(event.target.files)}
        />
      </div>

      {uploads.length > 0 && (
        <ul className="flex flex-col gap-2">
          {uploads.map((item) => (
            <li
              key={item.id}
              className="flex items-center justify-between gap-3 rounded-lg border border-white/10 bg-white/5 px-3 py-2 text-sm text-white/80"
            >
              <span className="truncate">{item.name}</span>
              {item.status === "uploading" && <LoadingSpinner size="sm" />}
              {item.status === "done" && <StatusBadge status="processing" />}
              {item.status === "error" && (
                <span className="shrink-0 text-xs text-status-critical">{item.message}</span>
              )}
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
