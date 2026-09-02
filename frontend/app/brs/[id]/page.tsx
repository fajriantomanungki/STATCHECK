"use client";

import { ArrowLeftIcon, CalendarDaysIcon, ChartBarSquareIcon, DocumentArrowUpIcon, PencilSquareIcon, UserGroupIcon } from "@heroicons/react/24/outline";
import Link from "next/link";
import { useParams } from "next/navigation";
import { useEffect, useState } from "react";

import { AppShell } from "@/components/app-shell";
import { getToken } from "@/lib/auth";
import { getBRS } from "@/services/api";
import type { BRS } from "@/types/phase2";

export default function BRSDetailPage() {
  const { id } = useParams<{ id: string }>();
  const [brs, setBrs] = useState<BRS | null>(null);
  const [error, setError] = useState("");
  useEffect(() => { const token = getToken(); if (token) getBRS(token, id).then(setBrs).catch((err) => setError(err.message)); }, [id]);

  return (
    <AppShell title="Detail BRS">
      <div className="p-6 lg:p-10">
        <Link href="/brs" className="inline-flex items-center gap-2 text-sm font-semibold text-slate-500 hover:text-cyan-700"><ArrowLeftIcon className="h-4 w-4" />Kembali ke daftar BRS</Link>
        {error && <p className="mt-5 rounded-lg bg-red-50 p-3 text-sm text-red-700">{error}</p>}
        {!brs ? <p className="mt-10 text-sm text-slate-400">Memuat detail BRS...</p> : <>
          <div className="mt-6 flex flex-col justify-between gap-5 rounded-2xl bg-[#102a43] p-7 text-white md:flex-row md:items-center"><div><div className="flex gap-2"><span className="rounded-full bg-white/10 px-3 py-1 text-xs">{brs.kode_brs}</span><span className="rounded-full bg-amber-400/20 px-3 py-1 text-xs font-semibold text-amber-200">{brs.status.toUpperCase()}</span></div><h1 className="mt-4 max-w-3xl text-3xl font-bold">{brs.nama_brs}</h1><p className="mt-2 text-sm text-slate-300">{brs.fungsi_pj}</p></div><div className="flex shrink-0 flex-wrap gap-3"><Link href={`/brs/${id}/edit`} className="flex items-center gap-2 rounded-xl border border-white/20 px-4 py-3 text-sm font-semibold hover:bg-white/10"><PencilSquareIcon className="h-5 w-5" />Edit</Link><Link href={`/brs/${id}/data`} className="flex items-center gap-2 rounded-xl border border-white/20 px-4 py-3 text-sm font-semibold hover:bg-white/10"><ChartBarSquareIcon className="h-5 w-5" />Kelola Data</Link><Link href={`/brs/${id}/documents`} className="flex items-center gap-2 rounded-xl bg-cyan-400 px-4 py-3 text-sm font-semibold text-[#102a43]"><DocumentArrowUpIcon className="h-5 w-5" />Kelola Dokumen</Link></div></div>

          <div className="mt-6 grid gap-5 md:grid-cols-2 xl:grid-cols-4">
            <section className="rounded-2xl border border-slate-200 bg-white p-6"><CalendarDaysIcon className="h-7 w-7 text-cyan-700" /><p className="mt-5 text-xs uppercase tracking-wider text-slate-400">Waktu Rilis</p><p className="mt-1 font-semibold text-slate-800">{new Intl.DateTimeFormat("id-ID", { dateStyle: "long" }).format(new Date(`${brs.waktu_rilis}T00:00:00`))}</p></section>
            <section className="rounded-2xl border border-slate-200 bg-white p-6"><UserGroupIcon className="h-7 w-7 text-cyan-700" /><p className="mt-5 text-xs uppercase tracking-wider text-slate-400">PJK / Supervisor</p><p className="mt-1 font-semibold text-slate-800">{brs.pjk.nama}</p><p className="mt-1 text-sm text-slate-500">Supervisor: {brs.supervisor?.nama || "Belum ditentukan"}</p></section>
            <section className="rounded-2xl border border-slate-200 bg-white p-6"><ChartBarSquareIcon className="h-7 w-7 text-cyan-700" /><p className="mt-5 text-xs uppercase tracking-wider text-slate-400">Data Indikator</p><p className="mt-1 text-3xl font-bold text-[#102a43]">{brs.jumlah_data}</p><p className="text-sm text-slate-500">data tersimpan</p></section>
            <section className="rounded-2xl border border-slate-200 bg-white p-6"><DocumentArrowUpIcon className="h-7 w-7 text-cyan-700" /><p className="mt-5 text-xs uppercase tracking-wider text-slate-400">Dokumen BRS</p><p className="mt-1 text-3xl font-bold text-[#102a43]">{brs.jumlah_dokumen}<span className="text-base font-medium text-slate-400">/3</span></p><p className="text-sm text-slate-500">dokumen aktif</p></section>
          </div>

          <section className="mt-6 rounded-2xl border border-slate-200 bg-white p-6"><h2 className="font-bold text-slate-800">Tim Penyusun</h2><div className="mt-4 grid gap-3 md:grid-cols-2 lg:grid-cols-3">{brs.team?.map((member) => <div key={member.id} className="rounded-xl bg-slate-50 p-4"><p className="font-semibold text-slate-700">{member.user.nama}</p><p className="mt-1 text-xs text-slate-400">{member.user.fungsi || member.role}</p></div>)}{!brs.team?.length && <p className="text-sm text-slate-400">Belum ada anggota tim tambahan.</p>}</div></section>
        </>}
      </div>
    </AppShell>
  );
}
