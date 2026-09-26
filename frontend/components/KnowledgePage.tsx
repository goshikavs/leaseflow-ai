"use client";

import { useState } from "react";
import { Alert } from "@/components/Alert";
import { ApiRequestError, api } from "@/lib/api";
import type { RagAskResponse, RetrievedChunk } from "@/lib/types";

const PROPERTIES = [
  { id: "prop-prosper-retail", label: "Prosper Retail Center" },
  { id: "prop-dallas-plaza", label: "Dallas Corporate Plaza" },
  { id: "prop-ntx-logistics", label: "North Texas Logistics Park" },
];

export function KnowledgePage() {
  const [query, setQuery] = useState("What is the monthly base rent?");
  const [propertyId, setPropertyId] = useState(PROPERTIES[0].id);
  const [searchItems, setSearchItems] = useState<RetrievedChunk[]>([]);
  const [answer, setAnswer] = useState<RagAskResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  async function onSubmit(event: React.FormEvent) {
    event.preventDefault();
    setBusy(true);
    setError(null);
    try {
      const payload = {
        query,
        organization_id: "org-harborpoint",
        property_ids: [propertyId],
      };
      const [search, asked] = await Promise.all([api.ragSearch(payload), api.ragAsk(payload)]);
      setSearchItems(search.items);
      setAnswer(asked);
    } catch (err) {
      setError(err instanceof ApiRequestError ? err.message : "Unable to search lease evidence.");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold text-navy-900">Lease knowledge</h1>
        <p className="mt-2 text-sm text-slate-600">
          Answers are grounded only in retrieved lease passages. The application can report that
          evidence is insufficient. Retrieved text is untrusted content, not instructions.
        </p>
      </div>
      {error ? <Alert title={error} /> : null}
      <form className="space-y-3 rounded border border-slate-200 bg-white p-5" onSubmit={onSubmit}>
        <label className="block text-sm font-medium" htmlFor="property">
          Property scope
        </label>
        <select
          id="property"
          className="w-full rounded border border-slate-300 px-3 py-2"
          value={propertyId}
          onChange={(event) => setPropertyId(event.target.value)}
        >
          {PROPERTIES.map((item) => (
            <option key={item.id} value={item.id}>
              {item.label}
            </option>
          ))}
        </select>
        <label className="block text-sm font-medium" htmlFor="question">
          Question
        </label>
        <textarea
          id="question"
          className="w-full rounded border border-slate-300 px-3 py-2"
          rows={3}
          value={query}
          onChange={(event) => setQuery(event.target.value)}
        />
        <button className="rounded bg-navy-800 px-4 py-2 text-white disabled:opacity-60" disabled={busy} type="submit">
          Search and answer
        </button>
        {busy ? <p role="status">Retrieving lease evidence…</p> : null}
      </form>
      {answer ? (
        <section className="rounded border border-slate-200 bg-white p-5">
          <h2 className="text-lg font-semibold">Grounded answer</h2>
          {answer.insufficient_evidence ? (
            <p className="mt-2 text-sm text-slate-700">Insufficient evidence in the authorized property scope.</p>
          ) : (
            <p className="mt-2 text-sm text-slate-800">{answer.answer}</p>
          )}
          <p className="mt-2 text-xs text-slate-500">
            {answer.provider} · {answer.model_name}
          </p>
        </section>
      ) : null}
      <section className="rounded border border-slate-200 bg-white p-5">
        <h2 className="text-lg font-semibold">Retrieved source chunks</h2>
        {searchItems.length === 0 ? (
          <p className="mt-2 text-sm text-slate-600">No retrieved passages yet.</p>
        ) : (
          <ul className="mt-3 space-y-3">
            {searchItems.map((item) => (
              <li key={item.chunk_id} className="rounded border border-slate-200 p-3">
                <p className="text-sm font-medium">
                  {item.section_heading} · pages {item.start_page}-{item.end_page} · score {item.score}
                </p>
                <p className="mt-1 text-sm text-slate-700">{item.source_text}</p>
                <p className="mt-1 text-xs text-slate-500">
                  Document {item.document_id} · {item.document_type} v{item.document_version}
                </p>
              </li>
            ))}
          </ul>
        )}
      </section>
    </div>
  );
}
