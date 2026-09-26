export type Stats = {
  total_documents: number;
  awaiting_review: number;
  approved_leases: number;
  processing_errors: number;
};

export type Page<T> = {
  items: T[];
  page: number;
  page_size: number;
  total: number;
};

export type DocumentSummary = {
  id: string;
  original_filename: string;
  content_hash: string;
  uploaded_at: string;
  processing_status: string;
  processing_error: string | null;
  lease_id: string | null;
};

export type ProcessResponse = {
  document: DocumentSummary;
  lease_id: string | null;
  extraction_id: string | null;
  validation_issue_count: number;
  blocking_issue_count: number;
  provider: string;
  fixture_mode: boolean;
};

export type LeaseSummary = {
  id: string;
  document_id: string;
  original_filename: string | null;
  tenant_name: string | null;
  landlord_name: string | null;
  property_address: string | null;
  status: string;
  version: number;
  created_at: string;
  updated_at: string;
  blocking_issue_count: number;
};

export type FieldEvidence = {
  field_name: string;
  page_number: number | null;
  source_text: string | null;
  extracted_value: string | null;
  confidence_status: string;
};

export type ValidationIssue = {
  id: string;
  field_name: string;
  issue_code: string;
  severity: string;
  description: string;
  resolved_at: string | null;
};

export type LeaseDetail = {
  id: string;
  document_id: string;
  original_filename: string | null;
  processing_status: string | null;
  tenant_name: string | null;
  landlord_name: string | null;
  property_address: string | null;
  commencement_date: string | null;
  expiration_date: string | null;
  monthly_base_rent: string | null;
  currency: string | null;
  renewal_notice_days: number | null;
  status: string;
  version: number;
  created_at: string;
  updated_at: string;
  approved_by: string | null;
  approved_at: string | null;
  extraction_provider: string | null;
  fixture_mode: boolean;
  organization_id?: string | null;
  property_id?: string | null;
  approval_source?: string | null;
  lease_type?: string | null;
  evidence: FieldEvidence[];
  issues: ValidationIssue[];
};

export type RetrievedChunk = {
  chunk_id: string;
  document_id: string;
  lease_id: string | null;
  organization_id: string;
  property_id: string;
  document_version: number;
  document_type: string;
  section_heading: string;
  start_page: number;
  end_page: number;
  source_text: string;
  score: number;
};

export type RagAskResponse = {
  answer: string;
  insufficient_evidence: boolean;
  citations: RetrievedChunk[];
  provider: string;
  model_name: string;
};

export type WorkflowOut = {
  id: string;
  lease_id: string;
  correlation_id: string;
  status: string;
  policy_result: string | null;
  recommendation: Record<string, unknown> | null;
  flag_version: number;
  agents: Array<{
    agent_name: string;
    status: string;
    findings: Record<string, unknown>;
    errors: unknown[];
    duration_ms: number;
  }>;
  tool_calls: Array<{
    server_name: string;
    tool_name: string;
    status: string;
    error: string | null;
    duration_ms: number;
    correlation_id: string;
  }>;
  policy_evaluations: Array<{
    decision: string;
    reason_codes: string[];
    conditions: Record<string, unknown>;
    dry_run: boolean;
    policy_version: number;
    lease_version: number;
  }>;
};

export type EffectiveFlags = {
  organization_id: string;
  property_id: string;
  lease_type?: string;
  config_version: number;
  flags: Record<string, boolean>;
  restricted: boolean;
  note: string;
};

export type AgentCatalogItem = {
  key: string;
  agent_name: string;
  label: string;
  mandatory: boolean;
  description: string;
};

export type LeaseTypeFlagSet = {
  lease_type: string;
  label: string;
  description: string;
  flags: Record<string, boolean>;
};

export type LeaseTypeFlagCatalog = {
  lease_types: LeaseTypeFlagSet[];
  agents: AgentCatalogItem[];
  note: string;
};

export type AuditEvent = {
  id: string;
  event_type: string;
  actor: string;
  change_details: Record<string, unknown>;
  occurred_at: string;
};

export type ExportPayload = {
  schema_version: string;
  source_system: string;
  lease_id: string;
  tenant: { name: string | null };
  property: { address: string | null };
  financial_terms: { monthly_base_rent: string | null; currency: string | null };
  important_dates: {
    commencement: string | null;
    expiration: string | null;
    renewal_notice_days: number | null;
  };
  review: { status: string; approved_by: string | null };
};

export type ApiError = {
  error: {
    code: string;
    message: string;
    details: Array<Record<string, unknown>>;
    correlation_id?: string | null;
  };
};
