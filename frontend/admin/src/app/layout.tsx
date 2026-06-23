import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "A.N.N. Admin Panel",
  description: "Internal administration dashboard for AI News Network",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" className="dark">
      <body className="min-h-screen bg-[#0a0a1a] text-white antialiased">
        <div className="flex min-h-screen">
          <aside className="w-64 border-r border-white/10 bg-[#0f0f1e] p-4">
            <div className="mb-8">
              <h1 className="text-lg font-bold text-indigo-400">A.N.N. Admin</h1>
              <p className="text-xs text-gray-500">Internal Dashboard</p>
            </div>
            <nav className="space-y-1">
              {[
                { href: "/", label: "Dashboard", icon: "📊" },
                { href: "/users", label: "Users", icon: "👥" },
                { href: "/moderation", label: "Moderation", icon: "🛡️" },
                { href: "/pipeline", label: "Pipeline", icon: "⚡" },
                { href: "/revenue", label: "Revenue", icon: "💰" },
                { href: "/services", label: "Services", icon: "🔧" },
                { href: "/settings", label: "Settings", icon: "⚙️" },
              ].map((item) => (
                <a
                  key={item.href}
                  href={item.href}
                  className="flex items-center gap-3 rounded-lg px-3 py-2 text-sm text-gray-400 hover:bg-white/5 hover:text-white"
                >
                  <span>{item.icon}</span>
                  {item.label}
                </a>
              ))}
            </nav>
          </aside>
          <main className="flex-1 p-8">{children}</main>
        </div>
      </body>
    </html>
  );
}
