"use client";

import { useRef, useState, type DragEvent } from "react";
import { UploadCloud, FileText, AlertCircle, Sparkles } from "lucide-react";
import { LoadingSpinner } from "@/components/ui/LoadingSpinner";
import { StatusBadge } from "@/components/ui/StatusBadge";
import { useToast } from "@/contexts/ToastContext";
import { apiClient, ApiError } from "@/lib/apiClient";
import {
  ACCEPTED_EXTENSIONS,
  MAX_FILE_SIZE_LABEL,
  validateUploadFile,
} from "@/lib/fileValidation";
import type { Document, DocumentUploadResponse } from "@/lib/types";
import { cn, formatBytes } from "@/lib/utils";

interface DropzoneProps {
  organizationId: string;
  docType?: Document["doc_type"];
  onUploaded?: (response: DocumentUploadResponse, fileName: string) => void;
}

interface UploadItem {
  id: string;
  name: string;
  size?: number;
  status: "uploading" | "done" | "error";
  message?: string;
}

export function Dropzone({ organizationId, docType = "other", onUploaded }: DropzoneProps) {
  const [isDragging, setIsDragging] = useState(false);
  const [uploads, setUploads] = useState<UploadItem[]>([]);
  const inputRef = useRef<HTMLInputElement>(null);
  const { showError, showSuccess } = useToast();

  async function uploadFile(file: File) {
    const id =
      typeof crypto !== "undefined" && typeof crypto.randomUUID === "function"
        ? crypto.randomUUID()
        : `${file.name}-${Date.now()}-${Math.random().toString(36).slice(2, 9)}`;

    const validationError = validateUploadFile(file);
    if (validationError) {
      setUploads((prev) => [
        ...prev,
        { id, name: file.name, size: file.size, status: "error", message: validationError },
      ]);
      showError(`"${file.name}" — ${validationError}`);
      return;
    }

    setUploads((prev) => [
      ...prev,
      { id, name: file.name, size: file.size, status: "uploading" },
    ]);

    try {
      const formData = new FormData();
      formData.append("organization", organizationId);
      formData.append("doc_type", docType);
      formData.append("file", file);

      const response = await apiClient.post<DocumentUploadResponse>(
        "/documents/",
        formData
      );

      setUploads((prev) =>
        prev.map((item) => (item.id === id ? { ...item, status: "done" } : item))
      );
      showSuccess(`"${file.name}" uploaded successfully. Dispatching agents...`);
      onUploaded?.(response, file.name);
    } catch (error) {
      const message =
        error instanceof ApiError ? `Upload failed (${error.status})` : "Upload failed";
      setUploads((prev) =>
        prev.map((item) => (item.id === id ? { ...item, status: "error", message } : item))
      );
      showError(`Couldn't upload "${file.name}" — ${message.toLowerCase()}.`);
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
        role="button"
        tabIndex={disabled ? -1 : 0}
        aria-disabled={disabled}
        onDragOver={(event) => {
          event.preventDefault();
          if (!disabled) setIsDragging(true);
        }}
        onDragLeave={() => setIsDragging(false)}
        onDrop={handleDrop}
        onClick={() => !disabled && inputRef.current?.click()}
        onKeyDown={(event) => {
          if (disabled) return;
          if (event.key === "Enter" || event.key === " ") {
            event.preventDefault();
            inputRef.current?.click();
          }
        }}
        className={cn(
          "group relative flex flex-col items-center justify-center rounded-2xl border-2 border-dashed px-6 py-10 text-center transition-all duration-200 backdrop-blur-md select-none",
          disabled
            ? "cursor-not-allowed border-white/[0.06] bg-white/[0.01] opacity-50"
            : isDragging
            ? "cursor-pointer border-indigo-400 bg-indigo-500/10 shadow-lg shadow-indigo-500/10 scale-[1.005]"
            : "cursor-pointer border-white/[0.12] bg-white/[0.02] hover:border-indigo-400/50 hover:bg-white/[0.04]"
        )}
      >
        <div
          className={cn(
            "flex h-12 w-12 items-center justify-center rounded-2xl border transition-all duration-200 mb-3",
            isDragging
              ? "border-indigo-400 bg-indigo-500/20 text-indigo-300 scale-110"
              : "border-white/10 bg-white/[0.04] text-white/50 group-hover:text-indigo-300 group-hover:border-indigo-500/30 group-hover:scale-105"
          )}
        >
          <UploadCloud className="h-6 w-6 stroke-[1.75]" />
        </div>

        <div>
          <p className="text-sm font-semibold text-white/90 group-hover:text-white flex items-center justify-center gap-1.5">
            <span>Drag and drop enterprise documents</span>
            <Sparkles className="h-3.5 w-3.5 text-indigo-400 opacity-80" />
          </p>
          <p className="mt-1 text-xs text-white/40">
            {disabled ? (
              <span className="text-amber-400/80">
                Please enter or select a valid Organization ID to enable intake
              </span>
            ) : (
              <span>
                Supported formats:{" "}
                <strong className="text-white/60">{ACCEPTED_EXTENSIONS.join(", ")}</strong> — up
                to {MAX_FILE_SIZE_LABEL}
              </span>
            )}
          </p>
        </div>

        <input
          ref={inputRef}
          type="file"
          multiple
          accept={ACCEPTED_EXTENSIONS.join(",")}
          disabled={disabled}
          className="hidden"
          onChange={(event) => {
            handleFiles(event.target.files);
            event.currentTarget.value = "";
          }}
        />
      </div>

      {uploads.length > 0 && (
        <ul className="flex flex-col gap-2">
          {uploads.map((item) => (
            <li
              key={item.id}
              className="flex items-center justify-between gap-3 rounded-xl border border-white/[0.08] bg-[#111116]/80 p-3 text-xs backdrop-blur-md"
            >
              <div className="flex items-center gap-2.5 min-w-0">
                <FileText className="h-4 w-4 text-indigo-400 shrink-0" />
                <span className="truncate font-medium text-white/90">{item.name}</span>
                {item.size && (
                  <span className="font-mono text-[11px] text-white/40">
                    ({formatBytes(item.size)})
                  </span>
                )}
              </div>

              <div className="shrink-0 flex items-center gap-2">
                {item.status === "uploading" && (
                  <div className="flex items-center gap-1.5 text-indigo-300 text-xs font-medium">
                    <LoadingSpinner size="xs" />
                    <span>Uploading…</span>
                  </div>
                )}
                {item.status === "done" && <StatusBadge status="processing" size="sm" />}
                {item.status === "error" && (
                  <span className="flex items-center gap-1 text-[11px] text-rose-400 font-medium">
                    <AlertCircle className="h-3 w-3" />
                    {item.message}
                  </span>
                )}
              </div>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
