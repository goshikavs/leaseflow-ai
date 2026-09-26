"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { Alert } from "@/components/Alert";
import { StatusBadge } from "@/components/StatusBadge";
import { ApiRequestError, api } from "@/lib/api";
import type { ExportPayload, LeaseDetail } from "@/lib/types";

export function ApprovedPage({ leaseId }: { leaseId: string }) {
  const [lease, setLease] = useState<LeaseDetail | null>(null);
  const [payload, setPayload] = useState<ExportPayload | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let cancelled = false;
    async function load() {
      try {
        const nextLease = await api.lease(leaseId);
        if (nextLease.status !== "approved") {
          if (!cancelled) {
            setLease(nextLease);
            setError("This lease is not approved, so export is unavailable.");
          }
          return;
        }
        const exported = await api.exportLease(leaseId);
        if (!cancelled) {
          setLease(nextLease);
          setPayload(exported);
        }
      } catch (err) {
        if (!cancelled) {
          setError(err instanceof ApiRequestError ? err.message : "Unable to load the approved lease.");
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

  if (loading) return <p role="status">Loading approved lease…</p>;
  if (error && !lease) return <Alert title={error} />;

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold text-navy-900">Approved lease export</h1>
        <p className="mt-2 text-sm text-slate-600">
          Versioned integration payload for downstream systems. Client-specific mappings should
          transform this contract rather than the extraction layer.
        </p>
      </div>
      {error ? <Alert title={error} /> : null}
      {lease ? (
        <section className="rounded border border-slate-200 bg-white p-5">
          <h2 className="text-lg font-semibold">Review information</h2>
          <dl className="mt-3 grid gap-2 text-sm sm:grid-cols-2">
            <div>
              <dt className="text-slate-500">Status</dt>
              <dd>
                <StatusBadge value={lease.status} />
              </dd>
            </div>
            <div>
              <dt className="text-slate-500">Approved by</dt>
              <dd>{lease.approved_by ?? "Not recorded"}</dd>
            </div>
            <div>
              <dt className="text-slate-500">Tenant</dt>
              <dd>{lease.tenant_name ?? "—"}</dd>
            </div>
            <div>
              <dt className="text-slate-500">Property</dt>
              <dd>{lease.property_address ?? "—"}</dd>
            </div>
          </dl>
          <p className="mt-4">
            <Link className="underline" href={`/leases/${lease.id}`}>
              Back to review
            </Link>
          </p>
        </section>
      ) : null}
      {payload ? (
        <section className="rounded border border-slate-200 bg-white p-5">
          <h2 className="text-lg font-semibold">Versioned JSON payload</h2>
          <p className="mt-1 text-sm text-slate-600">Schema version {payload.schema_version}</p>
          <pre className="mt-4 overflow-x-auto rounded bg-slate-950 p-4 text-xs text-slate-100">
            {JSON.stringify(payload, null, 2)}
          </pre>
        </section>
      ) : null}
    </div>
  );
}
