"use client";

import { CalendarDaysIcon, ChevronRightIcon, RocketLaunchIcon } from "@heroicons/react/24/outline";
import Link from "next/link";
import { useEffect, useState } from "react";

import { AppShell } from "@/components/app-shell";
import { getToken } from "@/lib/auth";
import { getReleases } from "@/services/api";
import type { Release } from "@/types/phase6";

export function ReleaseModuleList({ title, description, suffix, actionLabel }: { title: string; description: string; suffix: string; actionLabel: string }) {
  const [items, setItems] = useState<Release[]>([]);
  const [error, setError] = useState("");
  useEffect(() => { const token = getToken(); if (token) getReleases(token).then(setItems).catch((err) => setError(err.message)); }, []);

  return <AppShell title={title}><div className="p-6 lg:p-10"><div><p className="text-sm font-semibold uppercase tracking-widest text-cyan-700">Rilis</p><h1 className="mt-2 text-3xl font-bold text-slate-900">{title}</h1><p className="mt-2 text-slate-500">{description}</p></div>{error && <p className="mt-5 rounded-xl bg-red-50 p-4 text-red-700">{error}</p>}<div className="mt-7 space-y-4">{items.map((item) => <Link key={item.id} href={`/releases/${item.id}/${suffix}`} className="flex flex-col justify-between gap-4 rounded-2xl border border-slate-200 bg-white p-6 shadow-sm transition hover:border-cyan-400 sm:flex-row sm:items-center"><div><p className="text-xs font-bold uppercase tracking-wider text-cyan-700">{item.kode_rilis}</p><h2 className="mt-2 font-bold text-slate-800">{item.judul_rilis}</h2><p className="mt-2 flex items-center gap-2 text-sm text-slate-500"><CalendarDaysIcon className="h-4 w-4" />{new Intl.DateTimeFormat("id-ID", { dateStyle: "long" }).format(new Date(`${item.tanggal_rilis}T00:00:00`))} • {item.tempat}</p></div><span className="inline-flex items-center gap-2 text-sm font-semibold text-cyan-700">{actionLabel}<ChevronRightIcon className="h-4 w-4" /></span></Link>)}{!items.length && <div className="grid min-h-60 place-items-center rounded-2xl border border-dashed border-slate-300 bg-white text-center"><div><RocketLaunchIcon className="mx-auto h-10 w-10 text-slate-300" /><p className="mt-3 font-semibold text-slate-600">Belum ada kegiatan rilis.</p><Link href="/releases" className="mt-2 inline-block text-sm font-semibold text-cyan-700">Buka Release Center</Link></div></div>}</div></div></AppShell>;
}
