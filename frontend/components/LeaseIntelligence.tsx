"use client";

import { useEffect, useState } from "react";
import { StatusBadge } from "@/components/StatusBadge";
import { api } from "@/lib/api";
import type { EffectiveFlags, WorkflowOut } from "@/lib/types";

const TEAM_AGENTS = ["property", "finance", "legal", "leasing", "insurance"];

export function LeaseIntelligence({
  leaseId,
  organizationId,
  propertyId,
  leaseType = "commercial",
  approvalSource,
}: {
  leaseId: string;
  organizationId: string;
  propertyId: string;
  leaseType?: string;
  approvalSource?: string | null;
}) {
  const [workflow, setWorkflow] = useState<WorkflowOut | null>(null);
  const [flags, setFlags] = useState<EffectiveFlags | null>(null);
  const [mcp, setMcp] = useState<Record<string, { status: string; tools: string[] }>>({});
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let cancelled = false;
    async function load() {
      try {
        const [nextWorkflow, nextFlags, nextMcp] = await Promise.all([
          api.workflow(leaseId),
          api.flags(organizationId, propertyId, leaseType),
          api.mcpStatus(),
        ]);
        if (!cancelled) {
          setWorkflow(nextWorkflow);
          setFlags(nextFlags);
          setMcp(nextMcp.servers);
        }
      } catch (err) {
        if (!cancelled) setError(err instanceof Error ? err.message : "Unable to load agent context.");
      } finally {
        if (!cancelled) setLoading(false);
      }
    }
    void load();
    return () => {
      cancelled = true;
    };
  }, [leaseId, organizationId, propertyId, leaseType]);

  if (loading) return <p role="status">Loading agent and policy context…</p>;
  if (error) return <p className="text-sm text-slate-600">{error}</p>;

  const policy = workflow?.policy_evaluations.at(-1);
  const recommendation = workflow?.recommendation;

  return (
    <div className="grid gap-4 lg:grid-cols-2">
      <section className="rounded border border-slate-200 bg-white p-5">
        <h2 className="text-lg font-semibold">MCP team servers</h2>
        <p className="mt-1 text-xs text-slate-500">
          Catalog health for departmental tools. Document, lease RAG, and risk appear under Agent
          execution. Server status here does not mean specialists ran.
        </p>
        <ul className="mt-3 space-y-2 text-sm">
          {TEAM_AGENTS.map((name) => {
            const agent = workflow?.agents.find((item) => item.agent_name === name);
            const server = mcp[name];
            return (
              <li key={name} className="rounded border border-slate-200 p-3">
                <div className="flex items-center justify-between gap-2">
                  <p className="font-medium capitalize">{name} agent</p>
                  <StatusBadge
                    value={
                      !workflow
                        ? "not_run"
                        : (agent?.status.toLowerCase() ?? (name === "insurance" ? "optional" : "skipped"))
                    }
                  />
                </div>
                <p className="mt-1 text-xs text-slate-500">
                  MCP {server?.status ?? "unknown"}
                  {server?.tools?.length ? ` · ${server.tools.join(", ")}` : ""}
                </p>
              </li>
            );
          })}
        </ul>
      </section>
      <section className="rounded border border-slate-200 bg-white p-5">
        <h2 className="text-lg font-semibold">Agent execution</h2>
        <p className="mt-1 text-sm text-slate-600">
          Supervisor status: {workflow?.status ?? "not run"}
          {propertyId === "prop-unassigned"
            ? " · Agents start only for Property A/B/C samples, not unassigned uploads."
            : ` · ${propertyId}`}
        </p>
        {workflow?.agents.length ? (
          <ul className="mt-3 space-y-2 text-sm">
            {workflow.agents.map((agent) => (
              <li key={`${agent.agent_name}-${agent.status}`} className="flex items-center justify-between gap-2">
                <span className="capitalize">{agent.agent_name.replaceAll("_", " ")}</span>
                <span>
                  <StatusBadge value={agent.status.toLowerCase()} />
                  <span className="ml-2 text-xs text-slate-500">{agent.duration_ms} ms</span>
                </span>
              </li>
            ))}
          </ul>
        ) : (
          <p className="mt-2 text-sm text-slate-600">No specialist-agent execution recorded.</p>
        )}
      </section>
      <section className="rounded border border-slate-200 bg-white p-5">
        <h2 className="text-lg font-semibold">Approval control</h2>
        <p className="mt-2 text-sm">Lease type: {leaseType}</p>
        <p className="mt-1 text-sm">Property approval mode: {flags?.flags.REQUIRE_MANUAL_APPROVAL ? "manual only" : "policy controlled"}</p>
        <p className="mt-1 text-sm">
          AI recommendation: {String(recommendation?.recommendation ?? "none")} (advisory only)
        </p>
        <p className="mt-1 text-sm">
          Deterministic policy result: {policy?.decision ?? workflow?.policy_result ?? "not evaluated"}
        </p>
        <p className="mt-1 text-sm">Committed approval source: {approvalSource ?? "none"}</p>
        {policy?.reason_codes?.length ? (
          <ul className="mt-2 list-disc pl-5 text-sm">
            {policy.reason_codes.map((code) => (
              <li key={code}>{code}</li>
            ))}
          </ul>
        ) : null}
        <p className="mt-2 text-xs text-slate-500">
          Auto-approval is an internal abstraction decision only. It never signs a lease or commits funds.
        </p>
      </section>
      <section className="rounded border border-slate-200 bg-white p-5">
        <h2 className="text-lg font-semibold">Effective feature flags</h2>
        {flags ? (
          <ul className="mt-3 grid grid-cols-1 gap-1 text-sm sm:grid-cols-2">
            {Object.entries(flags.flags).map(([key, enabled]) => (
              <li key={key}>
                {key}: {enabled ? "on" : "off"}
              </li>
            ))}
          </ul>
        ) : (
          <p className="mt-2 text-sm text-slate-600">No flag configuration loaded.</p>
        )}
        <p className="mt-2 text-xs text-slate-500">{flags?.note}</p>
      </section>
    </div>
  );
}
