"use client";

import { ArrowRightStartOnRectangleIcon } from "@heroicons/react/24/outline";
import Link from "next/link";

import { Sidebar } from "@/components/sidebar";
import { useAuthUser } from "@/hooks/use-auth-user";

export function AppShell({ title, children }: { title: string; children: React.ReactNode }) {
  const { user, loading, logout } = useAuthUser();
  if (loading || !user) return <div className="grid min-h-screen place-items-center bg-slate-50 text-sm text-slate-500">Memuat STATCHECK...</div>;

  return (
    <main className="flex min-h-screen bg-[#f6f8fb]">
      <Sidebar />
      <section className="min-w-0 flex-1">
        <header className="flex items-center justify-between border-b border-slate-200 bg-white px-5 py-4 lg:px-10">
          <p className="font-bold text-[#102a43] lg:text-sm lg:font-medium lg:text-slate-500">{title}</p>
          <div className="flex items-center gap-3"><div className="text-right"><p className="text-sm font-semibold text-slate-800">{user.nama}</p><p className="text-xs uppercase tracking-wide text-slate-400">{user.user_level}</p></div><button onClick={logout} title="Keluar" className="rounded-lg border border-slate-200 p-2.5 text-slate-500 hover:bg-slate-50"><ArrowRightStartOnRectangleIcon className="h-5 w-5" /></button></div>
        </header>
        <nav className="flex gap-2 overflow-x-auto border-b border-slate-200 bg-white px-5 pb-3 lg:hidden">
          <Link href="/dashboard" className="rounded-lg bg-slate-100 px-3 py-2 text-xs font-medium">Dashboard</Link>
          <Link href="/brs" className="rounded-lg bg-slate-100 px-3 py-2 text-xs font-medium">BRS</Link>
          <Link href="/indicators" className="rounded-lg bg-slate-100 px-3 py-2 text-xs font-medium">Indikator</Link>
        </nav>
        {children}
      </section>
    </main>
  );
}
