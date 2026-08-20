export type DocumentType =
  | "security_questionnaire"
  | "invoice"
  | "compliance_log"
  | "other";

export type DocumentStatus = "pending" | "processing" | "completed" | "failed";

export interface DocumentUploadResponse {
  status: "processing";
  document_id: string;
}

export interface Document {
  id: string;
  organization: string;
  doc_type: DocumentType;
  status: DocumentStatus;
  file_path: string;
  created_at: string;
  updated_at: string;
  deleted_at: string | null;
}

export interface Answer {
  id: string;
  agent_run: string;
  question_text: string;
  content: string;
  confidence_score: number | null;
  is_verified: boolean;
  created_at: string;
  updated_at: string;
  deleted_at: string | null;
}

export interface ToolCall {
  id: string;
  agent_run: string;
  tool_name: string;
  input_data: Record<string, unknown>;
  output_data: Record<string, unknown>;
  created_at: string;
  updated_at: string;
  deleted_at: string | null;
}
