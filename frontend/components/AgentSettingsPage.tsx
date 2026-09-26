"use client";

import { useEffect, useState } from "react";
import { Alert } from "@/components/Alert";
import { ApiRequestError, api } from "@/lib/api";
import type { AgentCatalogItem, LeaseTypeFlagSet } from "@/lib/types";

export function AgentSettingsPage() {
  const [profiles, setProfiles] = useState<LeaseTypeFlagSet[]>([]);
  const [agents, setAgents] = useState<AgentCatalogItem[]>([]);
  const [note, setNote] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [notice, setNotice] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    api
      .leaseTypeFlags()
      .then((catalog) => {
        if (cancelled) return;
        setProfiles(catalog.lease_types);
        setAgents(catalog.agents);
        setNote(catalog.note);
      })
      .catch((err) => {
        if (!cancelled) {
          setError(err instanceof ApiRequestError ? err.message : "Unable to load agent settings.");
        }
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, []);

  function setFlag(leaseType: string, key: string, enabled: boolean) {
    setProfiles((current) =>
      current.map((profile) =>
        profile.lease_type === leaseType
          ? { ...profile, flags: { ...profile.flags, [key]: enabled } }
          : profile,
      ),
    );
  }

  async function save(leaseType: string) {
    const profile = profiles.find((item) => item.lease_type === leaseType);
    if (!profile) return;
    setSaving(leaseType);
    setError(null);
    setNotice(null);
    try {
      const result = await api.updateLeaseTypeFlags(leaseType, profile.flags);
      setProfiles((current) =>
        current.map((item) => (item.lease_type === leaseType ? { ...item, flags: result.flags } : item)),
      );
      setNotice(`${profile.label} agent settings saved.`);
    } catch (err) {
      setError(err instanceof ApiRequestError ? err.message : "Unable to save agent settings.");
    } finally {
      setSaving(null);
    }
  }

  if (loading) return <p role="status">Loading agent settings…</p>;

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold text-navy-900">Agent settings</h1>
        <p className="mt-2 text-sm text-slate-600">
          Choose which specialists run for commercial versus residential leases. The backend remains
          authoritative. Disabling a required agent skips that specialist and blocks auto-approval.
        </p>
      </div>
      {error ? <Alert title={error} /> : null}
      {notice ? <p role="status">{notice}</p> : null}
      <div className="grid gap-4 lg:grid-cols-2">
        {profiles.map((profile) => (
          <section key={profile.lease_type} className="rounded border border-slate-200 bg-white p-5">
            <h2 className="text-lg font-semibold">{profile.label} leases</h2>
            <p className="mt-1 text-sm text-slate-600">{profile.description}</p>
            <ul className="mt-4 space-y-3">
              {agents.map((agent) => {
                const enabled = Boolean(profile.flags[agent.key]);
                const inputId = `${profile.lease_type}-${agent.key}`;
                return (
                  <li key={agent.key} className="rounded border border-slate-200 p-3">
                    <div className="flex items-start justify-between gap-3">
                      <label className="block text-sm font-medium" htmlFor={inputId}>
                        {agent.label} agent
                        {agent.mandatory ? (
                          <span className="ml-2 text-xs font-normal text-slate-500">required</span>
                        ) : (
                          <span className="ml-2 text-xs font-normal text-slate-500">optional</span>
                        )}
                      </label>
                      <input
                        id={inputId}
                        type="checkbox"
                        checked={enabled}
                        onChange={(event) => setFlag(profile.lease_type, agent.key, event.target.checked)}
                      />
                    </div>
                    <p className="mt-1 text-xs text-slate-500">{agent.description}</p>
                    <p className="mt-1 text-xs text-slate-500">{enabled ? "Enabled" : "Disabled"}</p>
                  </li>
                );
              })}
            </ul>
            <button
              type="button"
              className="mt-4 rounded bg-navy-800 px-4 py-2 text-white disabled:opacity-60"
              disabled={saving === profile.lease_type}
              onClick={() => void save(profile.lease_type)}
            >
              Save {profile.label.toLowerCase()} settings
            </button>
          </section>
        ))}
      </div>
      {note ? <p className="text-xs text-slate-500">{note}</p> : null}
    </div>
  );
}
