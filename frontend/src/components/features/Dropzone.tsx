"use client";

import { useRef, useState, type DragEvent } from "react";

import { LoadingSpinner } from "@/components/ui/LoadingSpinner";
import { apiClient, ApiError } from "@/lib/apiClient";
import type { Document } from "@/lib/types";

interface DropzoneProps {
  organizationId: string;
  docType?: Document["doc_type"];
}

interface UploadItem {
  id: string;
  name: string;
  status: "uploading" | "done" | "error";
  message?: string;
}

export function Dropzone({ organizationId, docType = "other" }: DropzoneProps) {
  const [isDragging, setIsDragging] = useState(false);
  const [uploads, setUploads] = useState<UploadItem[]>([]);
  const inputRef = useRef<HTMLInputElement>(null);

  async function uploadFile(file: File) {
    const id = `${file.name}-${Date.now()}`;
    setUploads((prev) => [...prev, { id, name: file.name, status: "uploading" }]);

    try {
      const document = await apiClient.post<Document>("/documents/", {
        organization: organizationId,
        doc_type: docType,
        file_path: file.name,
      });
      setUploads((prev) =>
        prev.map((item) =>
          item.id === id
            ? { ...item, status: "done", message: document.status }
            : item,
        ),
      );
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

  return (
    <div className="flex flex-col gap-4">
      <div
        onDragOver={(event) => {
          event.preventDefault();
          setIsDragging(true);
        }}
        onDragLeave={() => setIsDragging(false)}
        onDrop={handleDrop}
        onClick={() => inputRef.current?.click()}
        className={`flex cursor-pointer flex-col items-center justify-center gap-2 rounded-xl border-2 border-dashed p-10 text-center transition-colors ${
          isDragging
            ? "border-indigo-400 bg-indigo-400/10"
            : "border-white/20 bg-white/5 hover:border-white/40"
        }`}
      >
        <p className="text-sm text-white/80">
          Drag and drop files here, or click to browse
        </p>
        <input
          ref={inputRef}
          type="file"
          multiple
          className="hidden"
          onChange={(event) => handleFiles(event.target.files)}
        />
      </div>

      {uploads.length > 0 && (
        <ul className="flex flex-col gap-2">
          {uploads.map((item) => (
            <li
              key={item.id}
              className="flex items-center justify-between rounded-lg border border-white/10 bg-white/5 px-3 py-2 text-sm text-white/80"
            >
              <span className="truncate">{item.name}</span>
              {item.status === "uploading" && <LoadingSpinner size="sm" />}
              {item.status === "done" && (
                <span className="text-emerald-400">{item.message}</span>
              )}
              {item.status === "error" && (
                <span className="text-red-400">{item.message}</span>
              )}
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
