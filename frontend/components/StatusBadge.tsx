const labels: Record<string, string> = {
  uploaded: "Uploaded",
  processing: "Processing",
  awaiting_review: "Awaiting review",
  approved: "Approved",
  failed: "Processing error",
  draft: "Draft",
  blocking: "Blocking",
  warning: "Warning",
  information: "Information",
  evidence_found: "Evidence found",
  missing: "Missing evidence",
  unsupported_evidence: "Unsupported evidence",
};

export function StatusBadge({ value }: { value: string }) {
  const label = labels[value] ?? value.replaceAll("_", " ");
  return (
    <span className="inline-flex items-center gap-2 rounded border border-slate-300 bg-white px-2 py-1 text-xs text-slate-800">
      <span aria-hidden="true" className="font-mono">
        {value === "blocking" || value === "failed" ? "!" : value === "approved" || value === "evidence_found" ? "OK" : "i"}
      </span>
      <span>{label}</span>
    </span>
  );
}
