"use client";

import { ArrowRightStartOnRectangleIcon, CheckCircleIcon, CircleStackIcon, ServerStackIcon, ShieldCheckIcon } from "@heroicons/react/24/outline";
import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";

import { Sidebar } from "@/components/sidebar";
import { clearToken, getToken } from "@/lib/auth";
import { getCurrentUser } from "@/services/api";
import type { User } from "@/types/auth";

const foundations = [
  { name: "Frontend", detail: "Next.js + TypeScript", icon: ServerStackIcon },
  { name: "Backend API", detail: "FastAPI", icon: CheckCircleIcon },
  { name: "Database", detail: "PostgreSQL", icon: CircleStackIcon },
  { name: "Authentication", detail: "JWT aktif", icon: ShieldCheckIcon },
];

export default function DashboardPage() {
  const router = useRouter();
  const [user, setUser] = useState<User | null>(null);

  useEffect(() => {
    const token = getToken();
    if (!token) { router.replace("/login"); return; }
    getCurrentUser(token).then(setUser).catch(() => { clearToken(); router.replace("/login"); });
  }, [router]);

  function logout() { clearToken(); router.replace("/login"); }

  if (!user) return <div className="grid min-h-screen place-items-center bg-slate-50 text-sm text-slate-500">Memuat STATCHECK...</div>;

  return (
    <main className="flex min-h-screen bg-[#f6f8fb]">
      <Sidebar />
      <section className="min-w-0 flex-1">
        <header className="flex items-center justify-between border-b border-slate-200 bg-white px-6 py-5 lg:px-10">
          <div><p className="font-bold text-[#102a43] lg:hidden">STATCHECK</p><p className="hidden text-sm text-slate-500 lg:block">Foundation Dashboard</p></div>
          <div className="flex items-center gap-4"><div className="text-right"><p className="text-sm font-semibold text-slate-800">{user.nama}</p><p className="text-xs uppercase tracking-wide text-slate-400">{user.user_level}</p></div><button onClick={logout} title="Keluar" className="rounded-lg border border-slate-200 p-2.5 text-slate-500 hover:bg-slate-50"><ArrowRightStartOnRectangleIcon className="h-5 w-5" /></button></div>
        </header>

        <div className="p-6 lg:p-10">
          <div className="rounded-2xl bg-gradient-to-r from-[#102a43] to-[#1e5278] p-7 text-white lg:p-9">
            <p className="text-sm font-medium text-cyan-200">PHASE 1 • FOUNDATION</p>
            <h1 className="mt-3 text-3xl font-semibold">Selamat datang, {user.nama.split(" ")[0]}.</h1>
            <p className="mt-3 max-w-2xl text-sm leading-6 text-slate-300">Fondasi STATCHECK telah aktif. Modul registrasi BRS, pemeriksaan dokumen, dan approval akan dibangun pada phase berikutnya.</p>
          </div>

          <h2 className="mt-9 text-lg font-bold text-slate-800">Status fondasi sistem</h2>
          <div className="mt-4 grid gap-4 md:grid-cols-2 xl:grid-cols-4">
            {foundations.map(({ name, detail, icon: Icon }) => (
              <article key={name} className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm shadow-slate-200/40"><div className="mb-5 grid h-11 w-11 place-items-center rounded-xl bg-cyan-50 text-cyan-700"><Icon className="h-6 w-6" /></div><p className="font-semibold text-slate-800">{name}</p><div className="mt-2 flex items-center justify-between"><p className="text-sm text-slate-500">{detail}</p><span className="rounded-full bg-emerald-50 px-2 py-1 text-[10px] font-bold uppercase text-emerald-700">Ready</span></div></article>
            ))}
          </div>

          <div className="mt-8 rounded-2xl border border-dashed border-slate-300 bg-white p-8 text-center"><p className="font-semibold text-slate-700">Modul BRS akan hadir pada Phase 2</p><p className="mt-2 text-sm text-slate-400">Registrasi BRS • Input Data • Master Indikator</p></div>
        </div>
      </section>
    </main>
  );
}
