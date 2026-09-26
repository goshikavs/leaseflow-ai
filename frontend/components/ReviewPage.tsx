"use client";

import Link from "next/link";
import { useEffect, useMemo, useState } from "react";
import { Alert } from "@/components/Alert";
import { StatusBadge } from "@/components/StatusBadge";
import { ApiRequestError, api } from "@/lib/api";
import type { AuditEvent, FieldEvidence, LeaseDetail } from "@/lib/types";

type FormState = {
  tenant_name: string;
  landlord_name: string;
  property_address: string;
  commencement_date: string;
  expiration_date: string;
  monthly_base_rent: string;
  currency: string;
  renewal_notice_days: string;
};

function toForm(lease: LeaseDetail): FormState {
  return {
    tenant_name: lease.tenant_name ?? "",
    landlord_name: lease.landlord_name ?? "",
    property_address: lease.property_address ?? "",
    commencement_date: lease.commencement_date ?? "",
    expiration_date: lease.expiration_date ?? "",
    monthly_base_rent: lease.monthly_base_rent ?? "",
    currency: lease.currency ?? "",
    renewal_notice_days: lease.renewal_notice_days?.toString() ?? "",
  };
}

export function ReviewPage({ leaseId }: { leaseId: string }) {
  const [lease, setLease] = useState<LeaseDetail | null>(null);
  const [audit, setAudit] = useState<AuditEvent[]>([]);
  const [form, setForm] = useState<FormState | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [notice, setNotice] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    let cancelled = false;
    async function load() {
      try {
        const [nextLease, nextAudit] = await Promise.all([api.lease(leaseId), api.audit(leaseId)]);
        if (!cancelled) {
          setLease(nextLease);
          setAudit(nextAudit);
          setForm(toForm(nextLease));
        }
      } catch (err) {
        if (!cancelled) {
          setError(err instanceof ApiRequestError ? err.message : "Unable to load lease.");
        }
      } finally {
        if (!cancelled) setLoading(false);
      }
    }
    void load();
    return () => {
      cancelled = true;
    };
  }, [leaseId]);

  const evidenceMap = useMemo(() => {
    const map = new Map<string, FieldEvidence>();
    lease?.evidence.forEach((item) => map.set(item.field_name, item));
    return map;
  }, [lease]);

  if (loading) return <p role="status">Loading lease review…</p>;
  if (error && !lease) return <Alert title={error} />;
  if (!lease || !form) return <Alert title="Lease not found." />;

  const currentLease = lease;
  const currentForm = form;
  const openIssues = currentLease.issues.filter((issue) => issue.resolved_at === null);
  const blockingCount = openIssues.filter((issue) => issue.severity === "blocking").length;
  const approved = currentLease.status === "approved";

  async function onSave(event: React.FormEvent) {
    event.preventDefault();
    setBusy(true);
    setError(null);
    setNotice(null);
    try {
      const updated = await api.saveLease(currentLease.id, {
        version: currentLease.version,
        tenant_name: currentForm.tenant_name || null,
        landlord_name: currentForm.landlord_name || null,
        property_address: currentForm.property_address || null,
        commencement_date: currentForm.commencement_date || null,
        expiration_date: currentForm.expiration_date || null,
        monthly_base_rent: currentForm.monthly_base_rent || null,
        currency: currentForm.currency || null,
        renewal_notice_days: currentForm.renewal_notice_days ? Number(currentForm.renewal_notice_days) : null,
      });
      setLease(updated);
      setForm(toForm(updated));
      setAudit(await api.audit(currentLease.id));
      setNotice("Corrections saved and the lease was revalidated.");
    } catch (err) {
      setError(err instanceof ApiRequestError ? err.message : "Save failed.");
    } finally {
      setBusy(false);
    }
  }

  async function onApprove() {
    setBusy(true);
    setError(null);
    setNotice(null);
    try {
      const updated = await api.approve(currentLease.id, currentLease.version, "demo-reviewer");
      setLease(updated);
      setAudit(await api.audit(currentLease.id));
      setNotice("Lease approved. Export is now available.");
    } catch (err) {
      setError(err instanceof ApiRequestError ? err.message : "Approval failed.");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div>
          <h1 className="text-2xl font-semibold text-navy-900">Lease review</h1>
          <p className="mt-1 text-sm text-slate-600">
            Document {lease.original_filename ?? lease.document_id}. Extracted values are drafts until
            approved. This is not legal advice.
          </p>
        </div>
        <div className="flex flex-col items-end gap-2">
          <StatusBadge value={lease.status} />
          {lease.fixture_mode ? (
            <p className="text-xs text-slate-600">Fixture extraction mode is active.</p>
          ) : null}
        </div>
      </div>
      {error ? <Alert title={error} /> : null}
      {notice ? (
        <p role="status" className="rounded border border-slate-300 bg-white p-3 text-sm">
          {notice}
        </p>
      ) : null}

      <div className="grid gap-6 lg:grid-cols-[minmax(0,1.2fr)_minmax(0,1fr)]">
        <form className="space-y-4 rounded border border-slate-200 bg-white p-5" onSubmit={onSave}>
          <h2 className="text-lg font-semibold">Extracted fields</h2>
          <Field
            id="tenant_name"
            label="Tenant name"
            value={form.tenant_name}
            disabled={approved}
            evidence={evidenceMap.get("tenant_name")}
            onChange={(value) => setForm({ ...form, tenant_name: value })}
          />
          <Field
            id="landlord_name"
            label="Landlord name"
            value={form.landlord_name}
            disabled={approved}
            evidence={evidenceMap.get("landlord_name")}
            onChange={(value) => setForm({ ...form, landlord_name: value })}
          />
          <Field
            id="property_address"
            label="Property address"
            value={form.property_address}
            disabled={approved}
            evidence={evidenceMap.get("property_address")}
            onChange={(value) => setForm({ ...form, property_address: value })}
          />
          <Field
            id="commencement_date"
            label="Commencement date"
            type="date"
            value={form.commencement_date}
            disabled={approved}
            evidence={evidenceMap.get("commencement_date")}
            onChange={(value) => setForm({ ...form, commencement_date: value })}
          />
          <Field
            id="expiration_date"
            label="Expiration date"
            type="date"
            value={form.expiration_date}
            disabled={approved}
            evidence={evidenceMap.get("expiration_date")}
            onChange={(value) => setForm({ ...form, expiration_date: value })}
          />
          <Field
            id="monthly_base_rent"
            label="Monthly base rent"
            value={form.monthly_base_rent}
            disabled={approved}
            evidence={evidenceMap.get("monthly_base_rent")}
            onChange={(value) => setForm({ ...form, monthly_base_rent: value })}
          />
          <Field
            id="currency"
            label="Currency"
            value={form.currency}
            disabled={approved}
            evidence={evidenceMap.get("currency")}
            onChange={(value) => setForm({ ...form, currency: value })}
          />
          <Field
            id="renewal_notice_days"
            label="Renewal notice days"
            value={form.renewal_notice_days}
            disabled={approved}
            evidence={evidenceMap.get("renewal_notice_days")}
            onChange={(value) => setForm({ ...form, renewal_notice_days: value })}
          />
          <div className="flex flex-wrap gap-3">
            <button
              type="submit"
              className="rounded bg-navy-800 px-4 py-2 text-white disabled:opacity-60"
              disabled={approved || busy}
            >
              Save corrections
            </button>
            <button
              type="button"
              className="rounded border border-slate-300 px-4 py-2 disabled:opacity-60"
              disabled={approved || busy || blockingCount > 0}
              onClick={() => void onApprove()}
            >
              Approve lease
            </button>
            {approved ? (
              <Link className="rounded border border-slate-300 px-4 py-2" href={`/leases/${lease.id}/approved`}>
                View approved export
              </Link>
            ) : null}
          </div>
          {blockingCount > 0 && !approved ? (
            <p className="text-sm text-slate-700">
              Approval is disabled because {blockingCount} blocking issue
              {blockingCount === 1 ? "" : "s"} remain.
            </p>
          ) : null}
        </form>

        <aside className="space-y-4">
          <section className="rounded border border-slate-200 bg-white p-5">
            <h2 className="text-lg font-semibold">Validation issues</h2>
            {openIssues.length === 0 ? (
              <p className="mt-2 text-sm text-slate-600">No open validation issues.</p>
            ) : (
              <ul className="mt-3 space-y-3">
                {openIssues.map((issue) => (
                  <li key={issue.id} className="rounded border border-slate-200 p-3">
                    <div className="flex items-center justify-between gap-2">
                      <p className="font-medium">{issue.field_name}</p>
                      <StatusBadge value={issue.severity} />
                    </div>
                    <p className="mt-1 text-sm text-slate-700">{issue.description}</p>
                    <p className="mt-1 text-xs text-slate-500">{issue.issue_code}</p>
                  </li>
                ))}
              </ul>
            )}
          </section>
          <section className="rounded border border-slate-200 bg-white p-5">
            <h2 className="text-lg font-semibold">Audit history</h2>
            {audit.length === 0 ? (
              <p className="mt-2 text-sm text-slate-600">No audit events yet.</p>
            ) : (
              <ol className="mt-3 space-y-3">
                {audit.map((event) => (
                  <li key={event.id}>
                    <p className="font-medium">{event.event_type.replaceAll("_", " ")}</p>
                    <p className="text-xs text-slate-500">
                      {event.actor} · {new Date(event.occurred_at).toLocaleString()}
                    </p>
                  </li>
                ))}
              </ol>
            )}
          </section>
        </aside>
      </div>
    </div>
  );
}

function Field({
  id,
  label,
  value,
  onChange,
  evidence,
  disabled,
  type = "text",
}: {
  id: string;
  label: string;
  value: string;
  onChange: (value: string) => void;
  evidence?: FieldEvidence;
  disabled: boolean;
  type?: string;
}) {
  return (
    <div>
      <label className="block text-sm font-medium" htmlFor={id}>
        {label}
      </label>
      <input
        id={id}
        name={id}
        type={type}
        className="mt-1 w-full rounded border border-slate-300 px-3 py-2"
        value={value}
        disabled={disabled}
        onChange={(event) => onChange(event.target.value)}
      />
      {evidence ? (
        <p className="mt-1 text-xs text-slate-600">
          <StatusBadge value={evidence.confidence_status} />
          {evidence.page_number ? ` Page ${evidence.page_number}.` : ""}{" "}
          {evidence.source_text ? `Evidence: “${evidence.source_text}”` : "No supporting passage stored."}
        </p>
      ) : (
        <p className="mt-1 text-xs text-slate-500">No extraction evidence for this field.</p>
      )}
    </div>
  );
}
