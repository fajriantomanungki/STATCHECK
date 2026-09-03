"use client";

import { CalendarDaysIcon, MapPinIcon, PlusIcon, RocketLaunchIcon, UserGroupIcon } from "@heroicons/react/24/outline";
import Link from "next/link";
import { useEffect, useState } from "react";

import { AppShell } from "@/components/app-shell";
import { useAuthUser } from "@/hooks/use-auth-user";
import { getToken } from "@/lib/auth";
import { getReleases } from "@/services/api";
import type { Release } from "@/types/phase6";

const statusLabel = { draft: "Persiapan", ongoing: "Sedang Berlangsung", completed: "Selesai" };
const statusStyle = { draft: "bg-amber-50 text-amber-700", ongoing: "bg-cyan-50 text-cyan-700", completed: "bg-emerald-50 text-emerald-700" };

export default function ReleasesPage() {
  const { user } = useAuthUser();
  const [items, setItems] = useState<Release[]>([]);
  const [error, setError] = useState("");
  useEffect(() => { const token = getToken(); if (token) getReleases(token).then(setItems).catch((err) => setError(err.message)); }, []);
  const canManage = user?.user_level === "admin" || user?.user_level === "humas";

  return <AppShell title="Release Center"><div className="p-6 lg:p-10">
    <div className="flex flex-col justify-between gap-5 md:flex-row md:items-end"><div><p className="text-sm font-semibold uppercase tracking-widest text-cyan-700">Phase 6</p><h1 className="mt-2 text-3xl font-bold text-slate-900">Release Center</h1><p className="mt-2 text-slate-500">Kelola kegiatan rilis, BRS siap rilis, dan daftar peserta.</p></div>{canManage && <Link href="/releases/new" className="inline-flex items-center justify-center gap-2 rounded-xl bg-[#102a43] px-5 py-3 font-semibold text-white"><PlusIcon className="h-5 w-5" />Buat Kegiatan Rilis</Link>}</div>
    {error && <p className="mt-5 rounded-xl bg-red-50 p-4 text-sm text-red-700">{error}</p>}
    <div className="mt-7 grid gap-5 lg:grid-cols-2">{items.map((item) => <Link key={item.id} href={`/releases/${item.id}`} className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm transition hover:border-cyan-400"><div className="flex items-start justify-between gap-4"><div><p className="text-xs font-bold uppercase tracking-wider text-cyan-700">{item.kode_rilis}</p><h2 className="mt-2 text-lg font-bold text-slate-800">{item.judul_rilis}</h2></div><span className={`shrink-0 rounded-full px-3 py-1 text-xs font-semibold ${statusStyle[item.status]}`}>{statusLabel[item.status]}</span></div><div className="mt-5 grid gap-3 text-sm text-slate-600 sm:grid-cols-2"><p className="flex items-center gap-2"><CalendarDaysIcon className="h-5 w-5 text-slate-400" />{new Intl.DateTimeFormat("id-ID", { dateStyle: "long" }).format(new Date(`${item.tanggal_rilis}T00:00:00`))} • {item.waktu_rilis.slice(0, 5)}</p><p className="flex items-center gap-2"><MapPinIcon className="h-5 w-5 text-slate-400" />{item.tempat}</p><p className="flex items-center gap-2"><RocketLaunchIcon className="h-5 w-5 text-slate-400" />{item.jumlah_brs} BRS</p><p className="flex items-center gap-2"><UserGroupIcon className="h-5 w-5 text-slate-400" />{item.jumlah_tamu} peserta</p></div></Link>)}{!items.length && <div className="col-span-full grid min-h-64 place-items-center rounded-2xl border border-dashed border-slate-300 bg-white text-center"><div><RocketLaunchIcon className="mx-auto h-12 w-12 text-slate-300" /><p className="mt-3 font-semibold text-slate-600">Belum ada kegiatan rilis.</p><p className="mt-1 text-sm text-slate-400">BRS harus disetujui Kepala BPS sebelum dapat dijadwalkan.</p></div></div>}</div>
  </div></AppShell>;
}

