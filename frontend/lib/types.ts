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
  evidence: FieldEvidence[];
  issues: ValidationIssue[];
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
