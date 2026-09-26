"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { Alert } from "@/components/Alert";
import { StatusBadge } from "@/components/StatusBadge";
import { ApiRequestError, api } from "@/lib/api";
import type { LeaseSummary, Stats } from "@/lib/types";

export function DashboardPage() {
  const [stats, setStats] = useState<Stats | null>(null);
  const [leases, setLeases] = useState<LeaseSummary[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let cancelled = false;
    async function load() {
      try {
        const [nextStats, nextLeases] = await Promise.all([api.stats(), api.leases()]);
        if (!cancelled) {
          setStats(nextStats);
          setLeases(nextLeases.items);
        }
      } catch (err) {
        if (!cancelled) {
          setError(err instanceof ApiRequestError ? err.message : "Unable to load dashboard data.");
        }
      } finally {
        if (!cancelled) setLoading(false);
      }
    }
    void load();
    return () => {
      cancelled = true;
    };
  }, []);

  if (loading) {
    return <p role="status">Loading dashboard…</p>;
  }
  if (error) {
    return <Alert title={error} />;
  }

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-2xl font-semibold text-navy-900">Lease review dashboard</h1>
        <p className="mt-2 max-w-3xl text-sm text-slate-600">
          Extracted lease data is a draft until a human reviewer approves it. This application does
          not provide legal advice.
        </p>
      </div>
      <section aria-label="Portfolio summary" className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <StatCard label="Total documents" value={stats?.total_documents ?? 0} />
        <StatCard label="Awaiting review" value={stats?.awaiting_review ?? 0} />
        <StatCard label="Approved leases" value={stats?.approved_leases ?? 0} />
        <StatCard label="Processing errors" value={stats?.processing_errors ?? 0} />
      </section>
      <section>
        <div className="mb-3 flex items-center justify-between">
          <h2 className="text-lg font-semibold">Recent lease records</h2>
          <Link className="text-sm text-navy-800 underline" href="/upload">
            Upload a lease
          </Link>
        </div>
        {leases.length === 0 ? (
          <p className="rounded border border-dashed border-slate-300 bg-white p-6 text-sm text-slate-600">
            No lease records yet. Upload a PDF to start a review.
          </p>
        ) : (
          <div className="overflow-x-auto rounded border border-slate-200 bg-white">
            <table className="min-w-full text-left text-sm">
              <thead className="bg-slate-100">
                <tr>
                  <th className="px-3 py-2 font-medium">Tenant</th>
                  <th className="px-3 py-2 font-medium">Document</th>
                  <th className="px-3 py-2 font-medium">Status</th>
                  <th className="px-3 py-2 font-medium">Blocking issues</th>
                  <th className="px-3 py-2 font-medium">Action</th>
                </tr>
              </thead>
              <tbody>
                {leases.map((lease) => (
                  <tr key={lease.id} className="border-t border-slate-200">
                    <td className="px-3 py-2">{lease.tenant_name ?? "Not extracted"}</td>
                    <td className="px-3 py-2">{lease.original_filename ?? lease.document_id}</td>
                    <td className="px-3 py-2">
                      <StatusBadge value={lease.status} />
                    </td>
                    <td className="px-3 py-2">{lease.blocking_issue_count}</td>
                    <td className="px-3 py-2">
                      <Link className="underline" href={`/leases/${lease.id}`}>
                        Open review
                      </Link>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </section>
    </div>
  );
}

function StatCard({ label, value }: { label: string; value: number }) {
  return (
    <article className="rounded border border-slate-200 bg-white p-4">
      <h2 className="text-sm text-slate-600">{label}</h2>
      <p className="mt-2 text-3xl font-semibold text-navy-900">{value}</p>
    </article>
  );
}
