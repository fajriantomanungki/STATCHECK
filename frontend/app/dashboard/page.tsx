"use client";

import { ChartBarSquareIcon, CircleStackIcon, DocumentArrowUpIcon, DocumentTextIcon, PencilSquareIcon, PlusIcon } from "@heroicons/react/24/outline";
import Link from "next/link";
import { useEffect, useState } from "react";

import { AppShell } from "@/components/app-shell";
import { useAuthUser } from "@/hooks/use-auth-user";
import { getToken } from "@/lib/auth";
import { getDashboardSummary } from "@/services/api";
import type { DashboardSummary } from "@/types/phase2";

const emptySummary: DashboardSummary = { total_brs: 0, draft_brs: 0, total_indicators: 0, total_brs_data: 0, total_documents: 0 };

export default function DashboardPage() {
  const { user } = useAuthUser();
  const [summary, setSummary] = useState(emptySummary);

  useEffect(() => {
    const token = getToken();
    if (token) getDashboardSummary(token).then(setSummary).catch(() => undefined);
  }, []);

  const cards = [
    { name: "Total BRS", value: summary.total_brs, detail: "BRS terdaftar", icon: DocumentTextIcon },
    { name: "BRS Draft", value: summary.draft_brs, detail: "Sedang disusun", icon: PencilSquareIcon },
    { name: "Master Indikator", value: summary.total_indicators, detail: "Indikator aktif", icon: CircleStackIcon },
    { name: "Data Indikator", value: summary.total_brs_data, detail: "Data tersimpan", icon: ChartBarSquareIcon },
    { name: "Dokumen Aktif", value: summary.total_documents, detail: "File terunggah", icon: DocumentArrowUpIcon },
  ];

  return (
    <AppShell title="Dashboard">
      <div className="p-6 lg:p-10">
        <div className="flex flex-col justify-between gap-5 rounded-2xl bg-gradient-to-r from-[#102a43] to-[#1e5278] p-7 text-white md:flex-row md:items-center lg:p-9">
          <div><p className="text-sm font-medium text-cyan-200">PHASE 2 • BRS MANAGEMENT</p><h1 className="mt-3 text-3xl font-semibold">Selamat datang, {user?.nama.split(" ")[0] ?? "Pengguna"}.</h1><p className="mt-3 max-w-2xl text-sm leading-6 text-slate-300">Daftarkan BRS, kelola master indikator, lalu masukkan data analisis dan fenomena secara terstruktur.</p></div>
          <Link href="/brs/new" className="flex shrink-0 items-center justify-center gap-2 rounded-xl bg-cyan-400 px-5 py-3 font-semibold text-[#102a43] hover:bg-cyan-300"><PlusIcon className="h-5 w-5" />Daftarkan BRS</Link>
        </div>

        <h2 className="mt-9 text-lg font-bold text-slate-800">Ringkasan Phase 4</h2>
        <div className="mt-4 grid gap-4 md:grid-cols-2 xl:grid-cols-5">
          {cards.map(({ name, value, detail, icon: Icon }) => (
            <article key={name} className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm shadow-slate-200/40"><div className="flex items-start justify-between"><div className="grid h-11 w-11 place-items-center rounded-xl bg-cyan-50 text-cyan-700"><Icon className="h-6 w-6" /></div><p className="text-3xl font-bold text-[#102a43]">{value}</p></div><p className="mt-5 font-semibold text-slate-800">{name}</p><p className="mt-1 text-sm text-slate-500">{detail}</p></article>
          ))}
        </div>

        <div className="mt-8 grid gap-4 md:grid-cols-2">
          <Link href="/brs" className="rounded-2xl border border-slate-200 bg-white p-6 transition hover:border-cyan-400"><p className="font-semibold text-slate-800">Kelola Berita Resmi Statistik</p><p className="mt-2 text-sm text-slate-500">Lihat BRS, tim penyusun, jadwal rilis, dan data indikator.</p></Link>
          <Link href="/indicators" className="rounded-2xl border border-slate-200 bg-white p-6 transition hover:border-cyan-400"><p className="font-semibold text-slate-800">Kelola Master Indikator</p><p className="mt-2 text-sm text-slate-500">Tambah indikator beserta kategori, satuan, dan fungsi penanggung jawab.</p></Link>
        </div>
      </div>
    </AppShell>
  );
}
