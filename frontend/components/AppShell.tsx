import Link from "next/link";

const links = [
  { href: "/", label: "Dashboard" },
  { href: "/upload", label: "Upload" },
  { href: "/knowledge", label: "Knowledge" },
  { href: "/settings", label: "Agent settings" },
];

export function AppShell({ children }: { children: React.ReactNode }) {
  return (
    <div className="min-h-screen">
      <a href="#main-content" className="skip-link rounded bg-navy-900 px-3 py-2 text-white">
        Skip to content
      </a>
      <header className="border-b border-slate-200 bg-white">
        <div className="mx-auto flex max-w-6xl items-center justify-between px-4 py-4">
          <div>
            <p className="text-xs uppercase tracking-wide text-slate-500">Commercial lease operations</p>
            <Link href="/" className="text-lg font-semibold text-navy-900">
              LeaseFlow AI
            </Link>
          </div>
          <nav aria-label="Primary">
            <ul className="flex gap-4 text-sm">
              {links.map((link) => (
                <li key={link.href}>
                  <Link className="text-slate-700 underline-offset-4 hover:underline" href={link.href}>
                    {link.label}
                  </Link>
                </li>
              ))}
            </ul>
          </nav>
        </div>
      </header>
      <main id="main-content" className="mx-auto max-w-6xl px-4 py-8">
        {children}
      </main>
    </div>
  );
}
