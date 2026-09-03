"use client";

import { ChartBarSquareIcon, CheckCircleIcon, DocumentTextIcon } from "@heroicons/react/24/outline";
import Link from "next/link";
import { useEffect, useState } from "react";

import { AppShell } from "@/components/app-shell";
import { getToken } from "@/lib/auth";
import { getBRSList } from "@/services/api";
import type { BRS } from "@/types/phase2";

const statusLabel: Record<string, string> = {
  draft: "Draft", data_completed: "Data Lengkap", documents_uploaded: "Siap Diperiksa",
  checking: "Sedang Diperiksa", pjk_review: "Review PJK", pjk_submitted: "Dikirim ke Supervisor",
  supervisor_review: "Review Supervisor", supervisor_revision: "Revisi Supervisor",
  supervisor_approved: "Disetujui Supervisor", ka_bps_review: "Review Kepala BPS",
  ka_bps_revision: "Revisi Kepala BPS", release_ready: "Siap Rilis", released: "Telah Dirilis",
};

export default function CheckingCenterPage() {
  const [items, setItems] = useState<BRS[]>([]);
  const [error, setError] = useState("");

  useEffect(() => {
    const token = getToken();
    if (token) getBRSList(token).then(setItems).catch((err) => setError(err.message));
  }, []);

  return (
    <AppShell title="Pemeriksaan">
      <div className="p-6 lg:p-10">
        <p className="text-sm font-semibold uppercase tracking-widest text-cyan-700">Phase 4</p>
        <h1 className="mt-2 text-3xl font-bold text-slate-900">Pusat Pemeriksaan</h1>
        <p className="mt-2 text-slate-500">Jalankan STATCHECK dan tindak lanjuti temuan untuk setiap BRS.</p>
        {error && <p className="mt-5 rounded-xl bg-red-50 p-4 text-sm text-red-700">{error}</p>}

        <div className="mt-7 overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-sm">
          <div className="overflow-x-auto"><table className="w-full text-left text-sm">
            <thead className="bg-slate-50 text-xs uppercase tracking-wide text-slate-500"><tr><th className="px-6 py-4">BRS</th><th className="px-6 py-4">Data</th><th className="px-6 py-4">Dokumen</th><th className="px-6 py-4">Status</th><th className="px-6 py-4"></th></tr></thead>
            <tbody className="divide-y divide-slate-100">
              {items.map((item) => {
                const ready = item.jumlah_data > 0 && item.jumlah_dokumen === 3 && ["documents_uploaded", "pjk_review"].includes(item.status);
                return <tr key={item.id} className="hover:bg-slate-50">
                  <td className="px-6 py-4"><p className="font-semibold text-[#102a43]">{item.nama_brs}</p><p className="mt-1 text-xs text-slate-400">{item.kode_brs}</p></td>
                  <td className="px-6 py-4"><span className="inline-flex items-center gap-1.5 text-slate-600"><ChartBarSquareIcon className="h-4 w-4" />{item.jumlah_data}</span></td>
                  <td className="px-6 py-4"><span className="inline-flex items-center gap-1.5 text-slate-600"><DocumentTextIcon className="h-4 w-4" />{item.jumlah_dokumen}/3</span></td>
                  <td className="px-6 py-4"><span className={`rounded-full px-3 py-1 text-xs font-semibold ${item.status === "pjk_review" ? "bg-cyan-50 text-cyan-700" : ready ? "bg-emerald-50 text-emerald-700" : "bg-amber-50 text-amber-700"}`}>{statusLabel[item.status] || item.status}</span></td>
                  <td className="px-6 py-4 text-right"><Link href={item.status === "documents_uploaded" || item.status === "pjk_review" || item.status.includes("revision") ? `/brs/${item.id}/checking` : `/brs/${item.id}/approval`} className="inline-flex items-center gap-2 rounded-lg bg-[#102a43] px-4 py-2 text-xs font-semibold text-white"><CheckCircleIcon className="h-4 w-4" />{item.status === "documents_uploaded" ? "Periksa" : item.status === "pjk_review" || item.status.includes("revision") ? "Lihat Hasil" : "Persetujuan"}</Link></td>
                </tr>;
              })}
              {!items.length && <tr><td colSpan={5} className="px-6 py-14 text-center text-slate-400">Belum ada BRS untuk diperiksa.</td></tr>}
            </tbody>
          </table></div>
        </div>
      </div>
    </AppShell>
  );
}
