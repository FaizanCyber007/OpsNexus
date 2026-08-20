import type { DocumentChatResponse } from "./types";

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000/api";

export class ApiError extends Error {
  status: number;
  body: unknown;

  constructor(status: number, body: unknown) {
    super(`API request failed with status ${status}`);
    this.name = "ApiError";
    this.status = status;
    this.body = body;
  }
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const isFormData = init?.body instanceof FormData;

  const res = await fetch(`${API_URL}${path}`, {
    ...init,
    headers: {
      ...(isFormData ? {} : { "Content-Type": "application/json" }),
      ...init?.headers,
    },
  });

  if (!res.ok) {
    let body: unknown;
    try {
      body = await res.json();
    } catch {
      body = res.statusText;
    }
    throw new ApiError(res.status, body);
  }

  if (res.status === 204) {
    return undefined as T;
  }

  return res.json() as Promise<T>;
}

export const apiClient = {
  get: <T>(path: string) => request<T>(path, { method: "GET" }),
  post: <T>(path: string, data?: unknown) =>
    request<T>(path, {
      method: "POST",
      body:
        data instanceof FormData
          ? data
          : data !== undefined
            ? JSON.stringify(data)
            : undefined,
    }),
  delete: <T = void>(path: string) => request<T>(path, { method: "DELETE" }),
  chatDocument: (
    documentId: string,
    data: { question: string; compare?: boolean },
  ) =>
    request<DocumentChatResponse>(`/v1/documents/${documentId}/chat/`, {
      method: "POST",
      body: JSON.stringify(data),
    }),
};
