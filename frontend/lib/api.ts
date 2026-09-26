import type {
  ApiError,
  AuditEvent,
  DocumentSummary,
  EffectiveFlags,
  ExportPayload,
  LeaseDetail,
  LeaseSummary,
  Page,
  ProcessResponse,
  RagAskResponse,
  RetrievedChunk,
  Stats,
  WorkflowOut,
} from "./types";

export const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export class ApiRequestError extends Error {
  status: number;
  code: string;

  constructor(message: string, status: number, code: string) {
    super(message);
    this.status = status;
    this.code = code;
  }
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_URL}${path}`, {
    ...init,
    headers: {
      ...(init?.body instanceof FormData ? {} : { "Content-Type": "application/json" }),
      ...init?.headers,
    },
  });
  if (!response.ok) {
    let code = "REQUEST_FAILED";
    let message = `Request failed (${response.status})`;
    try {
      const body = (await response.json()) as ApiError;
      code = body.error?.code ?? code;
      message = body.error?.message ?? message;
    } catch {
      // Keep the generic message when the server did not return JSON.
    }
    throw new ApiRequestError(message, response.status, code);
  }
  if (response.status === 204) {
    return undefined as T;
  }
  return (await response.json()) as T;
}

export const api = {
  stats: () => request<Stats>("/api/v1/stats"),
  leases: (status?: string) =>
    request<Page<LeaseSummary>>(`/api/v1/leases${status ? `?status=${encodeURIComponent(status)}` : ""}`),
  lease: (id: string) => request<LeaseDetail>(`/api/v1/leases/${id}`),
  audit: (id: string) => request<AuditEvent[]>(`/api/v1/leases/${id}/audit`),
  upload: (file: File) => {
    const body = new FormData();
    body.append("file", file);
    return request<DocumentSummary>("/api/v1/documents", { method: "POST", body });
  },
  uploadSample: (key: string) =>
    request<DocumentSummary>(`/api/v1/demo/samples/${key}/upload`, { method: "POST" }),
  process: (documentId: string) =>
    request<ProcessResponse>(`/api/v1/documents/${documentId}/process`, { method: "POST" }),
  saveLease: (id: string, payload: Record<string, unknown>) =>
    request<LeaseDetail>(`/api/v1/leases/${id}`, {
      method: "PATCH",
      body: JSON.stringify(payload),
    }),
  approve: (id: string, version: number, reviewedBy: string) =>
    request<LeaseDetail>(`/api/v1/leases/${id}/approve`, {
      method: "POST",
      body: JSON.stringify({ version, reviewed_by: reviewedBy }),
    }),
  exportLease: (id: string) => request<ExportPayload>(`/api/v1/leases/${id}/export`),
  ragSearch: (payload: {
    query: string;
    organization_id: string;
    property_ids: string[];
    lease_id?: string | null;
  }) =>
    request<{ items: RetrievedChunk[] }>("/api/v1/rag/search", {
      method: "POST",
      body: JSON.stringify(payload),
      headers: { "X-Organization-ID": payload.organization_id },
    }),
  ragAsk: (payload: {
    query: string;
    organization_id: string;
    property_ids: string[];
    lease_id?: string | null;
  }) =>
    request<RagAskResponse>("/api/v1/rag/ask", {
      method: "POST",
      body: JSON.stringify(payload),
      headers: { "X-Organization-ID": payload.organization_id },
    }),
  flags: (organizationId: string, propertyId: string) =>
    request<EffectiveFlags>(
      `/api/v1/flags/effective?organization_id=${encodeURIComponent(organizationId)}&property_id=${encodeURIComponent(propertyId)}`,
      { headers: { "X-Organization-ID": organizationId } },
    ),
  workflow: (leaseId: string) => request<WorkflowOut | null>(`/api/v1/leases/${leaseId}/workflow`),
  mcpStatus: () => request<{ transport: string; servers: Record<string, { status: string; tools: string[] }> }>(
    "/api/v1/mcp/status",
  ),
  timeline: (leaseId: string) =>
    request<{ events: AuditEvent[]; latest_policy_result: string | null; approval_source: string | null }>(
      `/api/v1/leases/${leaseId}/audit-timeline`,
    ),
};
