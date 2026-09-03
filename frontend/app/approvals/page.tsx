"use client";

import { ArrowRightIcon, CheckBadgeIcon, ClockIcon } from "@heroicons/react/24/outline";
import Link from "next/link";
import { useEffect, useMemo, useState } from "react";

import { AppShell } from "@/components/app-shell";
import { useAuthUser } from "@/hooks/use-auth-user";
import { getToken } from "@/lib/auth";
import { getBRSList } from "@/services/api";
import type { BRS } from "@/types/phase2";

const statusLabel: Record<string, string> = {
  pjk_review: "Pemeriksaan PJK", pjk_submitted: "Dikirim ke Supervisor",
  supervisor_review: "Pemeriksaan Supervisor", supervisor_revision: "Revisi Supervisor",
  supervisor_approved: "Disetujui Supervisor", ka_bps_review: "Pemeriksaan Kepala BPS",
  ka_bps_revision: "Revisi Kepala BPS", release_ready: "Siap Rilis",
};

const workflowStatuses = new Set(Object.keys(statusLabel));

export default function ApprovalCenterPage() {
  const { user } = useAuthUser();
  const [items, setItems] = useState<BRS[]>([]);
  const [error, setError] = useState("");

  useEffect(() => {
    const token = getToken();
    if (token) getBRSList(token).then(setItems).catch((err) => setError(err.message));
  }, []);

  const visible = useMemo(() => items.filter((item) => workflowStatuses.has(item.status)), [items]);
  const waiting = visible.filter((item) => {
    if (user?.user_level === "supervisor") return ["pjk_submitted", "supervisor_review"].includes(item.status);
    if (user?.user_level === "ka_bps") return item.status === "ka_bps_review";
    return ["pjk_review", "supervisor_approved", "supervisor_revision", "ka_bps_revision"].includes(item.status);
  }).length;

  return <AppShell title="Pusat Persetujuan">
    <div className="p-6 lg:p-10">
      <div className="flex flex-col justify-between gap-5 md:flex-row md:items-end">
        <div><p className="text-sm font-semibold uppercase tracking-widest text-cyan-700">Phase 5</p><h1 className="mt-2 text-3xl font-bold text-slate-900">Pusat Persetujuan</h1><p className="mt-2 text-slate-500">Kendalikan persetujuan PJK, Supervisor, dan Kepala BPS dalam satu audit trail.</p></div>
        <div className="flex items-center gap-3 rounded-2xl bg-[#102a43] px-5 py-4 text-white"><ClockIcon className="h-7 w-7 text-cyan-300" /><div><p className="text-2xl font-bold">{waiting}</p><p className="text-xs text-slate-300">menunggu tindakan Anda</p></div></div>
      </div>
      {error && <p className="mt-5 rounded-xl bg-red-50 p-4 text-sm text-red-700">{error}</p>}

      <div className="mt-7 overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-sm"><div className="overflow-x-auto"><table className="w-full text-left text-sm">
        <thead className="bg-slate-50 text-xs uppercase tracking-wide text-slate-500"><tr><th className="px-6 py-4">BRS</th><th className="px-6 py-4">Penanggung Jawab</th><th className="px-6 py-4">Status</th><th className="px-6 py-4"></th></tr></thead>
        <tbody className="divide-y divide-slate-100">
          {visible.map((item) => <tr key={item.id} className="hover:bg-slate-50"><td className="px-6 py-4"><p className="font-semibold text-[#102a43]">{item.nama_brs}</p><p className="mt-1 text-xs text-slate-400">{item.kode_brs} • Rilis {new Intl.DateTimeFormat("id-ID", { dateStyle: "medium" }).format(new Date(`${item.waktu_rilis}T00:00:00`))}</p></td><td className="px-6 py-4"><p className="text-slate-700">PJK: {item.pjk.nama}</p><p className="mt-1 text-xs text-slate-400">Supervisor: {item.supervisor?.nama || "Belum ditentukan"}</p></td><td className="px-6 py-4"><span className={`rounded-full px-3 py-1 text-xs font-semibold ${item.status === "release_ready" ? "bg-emerald-50 text-emerald-700" : item.status.includes("revision") ? "bg-red-50 text-red-700" : "bg-cyan-50 text-cyan-700"}`}>{statusLabel[item.status]}</span></td><td className="px-6 py-4 text-right"><Link href={`/brs/${item.id}/approval`} className="inline-flex items-center gap-2 rounded-lg bg-[#102a43] px-4 py-2 text-xs font-semibold text-white">Buka <ArrowRightIcon className="h-4 w-4" /></Link></td></tr>)}
          {!visible.length && <tr><td colSpan={4} className="px-6 py-14 text-center text-slate-400"><CheckBadgeIcon className="mx-auto mb-3 h-10 w-10 text-slate-300" />Belum ada BRS dalam alur persetujuan.</td></tr>}
        </tbody>
      </table></div></div>
    </div>
  </AppShell>;
}

