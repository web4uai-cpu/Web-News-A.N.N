"use client";

import { useState } from "react";

type Role = "super_admin" | "editor" | "viewer";

interface User {
  id: string;
  email: string;
  role: Role;
  status: "active" | "suspended";
  plan: string;
  created_at: string;
  last_login: string;
}

const MOCK_USERS: User[] = [
  { id: "u1", email: "admin@ann.news", role: "super_admin", status: "active", plan: "Enterprise", created_at: "2026-01-15", last_login: "2026-06-23" },
  { id: "u2", email: "editor@ann.news", role: "editor", status: "active", plan: "Creator", created_at: "2026-02-20", last_login: "2026-06-22" },
  { id: "u3", email: "client@newscorp.com", role: "viewer", status: "active", plan: "Business Pro", created_at: "2026-03-10", last_login: "2026-06-21" },
  { id: "u4", email: "suspended@spam.com", role: "viewer", status: "suspended", plan: "Free", created_at: "2026-04-01", last_login: "2026-05-01" },
];

const ROLE_COLORS: Record<Role, string> = {
  super_admin: "bg-red-500/20 text-red-400",
  editor: "bg-amber-500/20 text-amber-400",
  viewer: "bg-blue-500/20 text-blue-400",
};

export default function UsersPage() {
  const [users] = useState(MOCK_USERS);
  const [search, setSearch] = useState("");

  const filtered = users.filter((u) =>
    u.email.toLowerCase().includes(search.toLowerCase())
  );

  return (
    <div>
      <div className="mb-6 flex items-center justify-between">
        <h1 className="text-2xl font-bold">User Management</h1>
        <input
          type="text"
          placeholder="Search users..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          className="rounded-lg border border-white/10 bg-white/5 px-3 py-2 text-sm outline-none focus:border-indigo-500"
        />
      </div>

      <div className="rounded-xl border border-white/10 bg-[#0f0f1e] overflow-hidden">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-white/10 text-left text-xs text-gray-500">
              <th className="px-4 py-3">Email</th>
              <th className="px-4 py-3">Role</th>
              <th className="px-4 py-3">Status</th>
              <th className="px-4 py-3">Plan</th>
              <th className="px-4 py-3">Last Login</th>
              <th className="px-4 py-3">Actions</th>
            </tr>
          </thead>
          <tbody>
            {filtered.map((user) => (
              <tr key={user.id} className="border-b border-white/5 hover:bg-white/5">
                <td className="px-4 py-3">{user.email}</td>
                <td className="px-4 py-3">
                  <span className={`rounded-full px-2 py-0.5 text-xs ${ROLE_COLORS[user.role]}`}>
                    {user.role}
                  </span>
                </td>
                <td className="px-4 py-3">
                  <span className={`rounded-full px-2 py-0.5 text-xs ${
                    user.status === "active" ? "bg-green-500/20 text-green-400" : "bg-red-500/20 text-red-400"
                  }`}>
                    {user.status}
                  </span>
                </td>
                <td className="px-4 py-3 text-gray-400">{user.plan}</td>
                <td className="px-4 py-3 text-gray-500">{user.last_login}</td>
                <td className="px-4 py-3">
                  <button className="mr-2 text-xs text-indigo-400 hover:text-indigo-300">Edit</button>
                  <button className="text-xs text-red-400 hover:text-red-300">
                    {user.status === "active" ? "Suspend" : "Reactivate"}
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
