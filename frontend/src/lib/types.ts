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
  latest_agent_run_id: string | null;
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
  tool_input: unknown;
  tool_output: unknown;
  created_at: string;
}
