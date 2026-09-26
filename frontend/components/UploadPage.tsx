"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";
import { Alert } from "@/components/Alert";
import { ApiRequestError, api } from "@/lib/api";

const MAX_BYTES = 10 * 1024 * 1024;
const samples = [
  { key: "sample_lease", label: "Complete valid lease" },
  { key: "missing_fields_lease", label: "Missing fields lease" },
  { key: "conflicting_dates_lease", label: "Conflicting dates lease" },
  { key: "prosper_retail_lease", label: "Property A: Prosper Retail Center" },
  { key: "dallas_plaza_lease", label: "Property B: Dallas Corporate Plaza" },
  { key: "logistics_park_lease", label: "Property C: North Texas Logistics Park" },
  { key: "logistics_park_amendment", label: "Property C amendment" },
];

export function UploadPage() {
  const router = useRouter();
  const [file, setFile] = useState<File | null>(null);
  const [leaseType, setLeaseType] = useState("commercial");
  const [status, setStatus] = useState<string>("");
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  async function run(upload: () => Promise<{ id: string }>) {
    setBusy(true);
    setError(null);
    try {
      setStatus("Uploading document…");
      const document = await upload();
      setStatus("Extracting and validating fields…");
      const processed = await api.process(document.id);
      if (!processed.lease_id) {
        throw new Error("Processing completed without a lease record.");
      }
      setStatus("Opening review…");
      router.push(`/leases/${processed.lease_id}`);
    } catch (err) {
      setError(err instanceof ApiRequestError || err instanceof Error ? err.message : "Upload failed.");
      setStatus("");
    } finally {
      setBusy(false);
    }
  }

  function onFile(next: File | null) {
    setError(null);
    if (!next) {
      setFile(null);
      return;
    }
    if (!next.name.toLowerCase().endsWith(".pdf")) {
      setError("Only PDF files are accepted.");
      setFile(null);
      return;
    }
    if (next.size > MAX_BYTES) {
      setError("File exceeds the 10 MB upload limit.");
      setFile(null);
      return;
    }
    setFile(next);
  }

  return (
    <div className="max-w-3xl space-y-6">
      <div>
        <h1 className="text-2xl font-semibold text-navy-900">Upload a commercial lease</h1>
        <p className="mt-2 text-sm text-slate-600">
          PDF files up to 10 MB. Extraction uses the configured provider. The default demo uses
          deterministic fixture extraction and does not call a live LLM.
        </p>
      </div>
      {error ? <Alert title={error} /> : null}
      {status ? <p role="status">{status}</p> : null}
      <form
        className="space-y-4 rounded border border-slate-200 bg-white p-6"
        onSubmit={(event) => {
          event.preventDefault();
          if (file) void run(() => api.upload(file, leaseType));
        }}
      >
        <label className="block text-sm font-medium" htmlFor="lease-file">
          Lease PDF
        </label>
        <input
          id="lease-file"
          name="lease-file"
          type="file"
          accept="application/pdf,.pdf"
          onChange={(event) => onFile(event.target.files?.[0] ?? null)}
        />
        <label className="block text-sm font-medium" htmlFor="lease-type">
          Lease type
        </label>
        <select
          id="lease-type"
          className="w-full rounded border border-slate-300 px-3 py-2"
          value={leaseType}
          onChange={(event) => setLeaseType(event.target.value)}
        >
          <option value="commercial">Commercial</option>
          <option value="residential">Residential</option>
        </select>
        <p className="text-sm text-slate-600">
          Agent enablement is configured per lease type on Agent settings. Current selection: {leaseType}.
        </p>
        <p className="text-sm text-slate-600">{file ? `Selected: ${file.name}` : "No file selected."}</p>
        <button
          type="submit"
          className="rounded bg-navy-800 px-4 py-2 text-white disabled:cursor-not-allowed disabled:opacity-60"
          disabled={!file || busy}
        >
          Upload and process
        </button>
      </form>
      <section className="rounded border border-slate-200 bg-white p-6">
        <h2 className="text-lg font-semibold">Use a synthetic sample</h2>
        <p className="mt-1 text-sm text-slate-600">
          Use Property A, B, or C to run specialists, MCP, and policy. The first three samples stay
          unassigned and only exercise human review. These files are fictional and are not live LLM
          results.
        </p>
        <div className="mt-4 flex flex-col gap-2 sm:flex-row">
          {samples.map((sample) => (
            <button
              key={sample.key}
              type="button"
              className="rounded border border-slate-300 px-3 py-2 text-sm disabled:opacity-60"
              disabled={busy}
              onClick={() => void run(() => api.uploadSample(sample.key, leaseType))}
            >
              {sample.label}
            </button>
          ))}
        </div>
      </section>
    </div>
  );
}
