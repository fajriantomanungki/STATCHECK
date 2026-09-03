"use client";

import { MagnifyingGlassIcon, PlusIcon } from "@heroicons/react/24/outline";
import Link from "next/link";
import { FormEvent, useCallback, useEffect, useState } from "react";

import { AppShell } from "@/components/app-shell";
import { getToken } from "@/lib/auth";
import { getBRSList } from "@/services/api";
import type { BRS } from "@/types/phase2";

const statusLabel: Record<string, string> = {
  draft: "Draft", data_completed: "Data Lengkap", documents_uploaded: "Dokumen Lengkap", checking: "Pemeriksaan Sistem",
  pjk_review: "Pemeriksaan PJK", pjk_submitted: "Dikirim ke Supervisor", supervisor_review: "Pemeriksaan Supervisor",
  supervisor_revision: "Revisi Supervisor", supervisor_approved: "Disetujui Supervisor", ka_bps_review: "Pemeriksaan Kepala BPS",
  ka_bps_revision: "Revisi Kepala BPS", release_ready: "Siap Rilis",
};

export default function BRSPage() {
  const [items, setItems] = useState<BRS[]>([]);
  const [search, setSearch] = useState("");
  const [error, setError] = useState("");

  const load = useCallback(async (query = "") => { const token = getToken(); if (token) setItems(await getBRSList(token, query)); }, []);
  useEffect(() => {
    const token = getToken();
    if (token) getBRSList(token).then(setItems).catch((err) => setError(err.message));
  }, []);
  function submit(event: FormEvent) { event.preventDefault(); load(search).catch((err) => setError(err.message)); }

  return (
    <AppShell title="Berita Resmi Statistik">
      <div className="p-6 lg:p-10">
        <div className="flex flex-col justify-between gap-4 md:flex-row md:items-end"><div><p className="text-sm font-semibold uppercase tracking-widest text-cyan-700">Phase 5</p><h1 className="mt-2 text-3xl font-bold text-slate-900">Daftar BRS</h1><p className="mt-2 text-slate-500">Kelola registrasi, data, dokumen, pemeriksaan, dan persetujuan Berita Resmi Statistik.</p></div><Link href="/brs/new" className="flex items-center justify-center gap-2 rounded-xl bg-[#102a43] px-5 py-3 font-semibold text-white"><PlusIcon className="h-5 w-5" />Tambah BRS</Link></div>
        <form onSubmit={submit} className="mt-7 flex max-w-xl rounded-xl border border-slate-200 bg-white p-2 shadow-sm"><MagnifyingGlassIcon className="ml-2 h-5 w-5 self-center text-slate-400" /><input value={search} onChange={(e) => setSearch(e.target.value)} className="min-w-0 flex-1 px-3 py-2 outline-none" placeholder="Cari nama BRS..." /><button className="rounded-lg bg-cyan-50 px-4 py-2 text-sm font-semibold text-cyan-800">Cari</button></form>
        {error && <p className="mt-5 rounded-lg bg-red-50 p-3 text-sm text-red-700">{error}</p>}

        <div className="mt-6 overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-sm"><div className="overflow-x-auto"><table className="w-full text-left text-sm"><thead className="bg-slate-50 text-xs uppercase tracking-wide text-slate-500"><tr><th className="px-6 py-4">BRS</th><th className="px-6 py-4">Waktu Rilis</th><th className="px-6 py-4">PJK / Supervisor</th><th className="px-6 py-4">Data</th><th className="px-6 py-4">Dokumen</th><th className="px-6 py-4">Status</th></tr></thead><tbody className="divide-y divide-slate-100">
          {items.map((item) => <tr key={item.id} className="hover:bg-slate-50"><td className="px-6 py-4"><Link href={`/brs/${item.id}`} className="font-semibold text-[#102a43] hover:text-cyan-700">{item.nama_brs}</Link><p className="mt-1 text-xs text-slate-400">{item.kode_brs} • {item.fungsi_pj}</p></td><td className="px-6 py-4 text-slate-600">{new Intl.DateTimeFormat("id-ID", { dateStyle: "long" }).format(new Date(`${item.waktu_rilis}T00:00:00`))}</td><td className="px-6 py-4 text-slate-600"><p>{item.pjk.nama}</p><p className="text-xs text-slate-400">{item.supervisor?.nama || "Supervisor belum ditentukan"}</p></td><td className="px-6 py-4 font-semibold text-slate-700">{item.jumlah_data}</td><td className="px-6 py-4 font-semibold text-slate-700">{item.jumlah_dokumen}/3</td><td className="px-6 py-4"><span className="rounded-full bg-amber-50 px-3 py-1 text-xs font-semibold text-amber-700">{statusLabel[item.status] || item.status}</span></td></tr>)}
          {!items.length && <tr><td colSpan={6} className="px-6 py-14 text-center text-slate-400">Belum ada BRS yang terdaftar.</td></tr>}
        </tbody></table></div></div>
      </div>
    </AppShell>
  );
}
