import { z } from "zod";

export const ACCEPTED_EXTENSIONS = [".pdf", ".csv", ".xlsx"] as const;
export const MAX_FILE_SIZE_BYTES = 10 * 1024 * 1024;
export const MAX_FILE_SIZE_LABEL = "10MB";

function hasAcceptedExtension(file: File): boolean {
  const name = file.name.toLowerCase();
  return ACCEPTED_EXTENSIONS.some((ext) => name.endsWith(ext));
}

export const fileUploadSchema = z
  .instanceof(File)
  .refine(hasAcceptedExtension, {
    message: `Only ${ACCEPTED_EXTENSIONS.join(", ")} files are supported.`,
  })
  .refine((file) => file.size <= MAX_FILE_SIZE_BYTES, {
    message: `File is larger than ${MAX_FILE_SIZE_LABEL}.`,
  });

export function validateUploadFile(file: File): string | null {
  const result = fileUploadSchema.safeParse(file);
  if (result.success) return null;
  return result.error.issues[0]?.message ?? "This file can't be uploaded.";
}
