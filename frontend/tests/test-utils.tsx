import { render, type RenderOptions } from "@testing-library/react";
import type { ReactElement } from "react";
import type { LeaseDetail } from "@/lib/types";

export function renderUi(ui: ReactElement, options?: RenderOptions) {
  return render(ui, options);
}

export function jsonResponse(data: unknown, status = 200): Response {
  return new Response(JSON.stringify(data), {
    status,
    headers: { "Content-Type": "application/json" },
  });
}

export const emptyStats = {
  total_documents: 0,
  awaiting_review: 0,
  approved_leases: 0,
  processing_errors: 0,
};

export const sampleLease: LeaseDetail = {
  id: "lease-1",
  document_id: "doc-1",
  original_filename: "sample_lease.pdf",
  processing_status: "awaiting_review",
  tenant_name: "Northwind Analytics LLC",
  landlord_name: "Harborpoint Realty Partners LLC",
  property_address: "1200 Commerce Street, Suite 400, Dallas, TX 75201",
  commencement_date: "2026-01-01",
  expiration_date: "2028-12-31",
  monthly_base_rent: "18500.00",
  currency: "USD",
  renewal_notice_days: 180,
  status: "awaiting_review",
  version: 1,
  created_at: "2026-04-20T12:00:00Z",
  updated_at: "2026-04-20T12:00:00Z",
  approved_by: null,
  approved_at: null,
  extraction_provider: "fixture",
  fixture_mode: true,
  evidence: [
    {
      field_name: "tenant_name",
      page_number: 1,
      source_text: "Tenant: Northwind Analytics LLC",
      extracted_value: "Northwind Analytics LLC",
      confidence_status: "evidence_found",
    },
  ],
  issues: [
    {
      id: "issue-1",
      field_name: "property_address",
      issue_code: "MISSING_PROPERTY",
      severity: "blocking",
      description: "Property address is required before approval.",
      resolved_at: null,
    },
  ],
};
