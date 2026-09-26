export function Alert({
  title,
  children,
  tone = "error",
}: {
  title: string;
  children?: React.ReactNode;
  tone?: "error" | "info";
}) {
  return (
    <div
      role={tone === "error" ? "alert" : "status"}
      className="rounded border border-slate-300 bg-white p-4"
    >
      <p className="font-semibold text-slate-900">
        {tone === "error" ? "Error: " : ""}
        {title}
      </p>
      {children ? <div className="mt-2 text-sm text-slate-700">{children}</div> : null}
    </div>
  );
}
