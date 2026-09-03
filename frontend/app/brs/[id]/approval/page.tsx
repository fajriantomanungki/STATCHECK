"use client";

import { ArrowLeftIcon, ArrowPathIcon, CheckBadgeIcon, CheckCircleIcon, DocumentTextIcon, PaperAirplaneIcon, XMarkIcon } from "@heroicons/react/24/outline";
import Link from "next/link";
import { useParams } from "next/navigation";
import { useEffect, useMemo, useState } from "react";

import { AppShell } from "@/components/app-shell";
import { useAuthUser } from "@/hooks/use-auth-user";
import { getToken } from "@/lib/auth";
import { getApprovalWorkflow, getBRS, kaBpsApprove, kaBpsRevision, startSupervisorReview, submitKaBps, submitSupervisor, supervisorApprove, supervisorRevision } from "@/services/api";
import type { BRS } from "@/types/phase2";
import type { ApprovalWorkflow } from "@/types/phase5";

const statusLabel: Record<string, string> = {
  pjk_review: "Pemeriksaan PJK", pjk_submitted: "Dikirim ke Supervisor",
  supervisor_review: "Pemeriksaan Supervisor", supervisor_revision: "Revisi Supervisor",
  supervisor_approved: "Disetujui Supervisor", ka_bps_review: "Pemeriksaan Kepala BPS",
  ka_bps_revision: "Revisi Kepala BPS", release_ready: "Siap Rilis", released: "Telah Dirilis",
};
const actionLabel: Record<string, string> = {
  submitted: "PJK mengirim ke Supervisor", review_started: "Supervisor memulai pemeriksaan",
  approved: "Dokumen disetujui", revision: "Dokumen dikembalikan untuk revisi",
  submitted_to_ka_bps: "Dokumen dikirim ke Kepala BPS",
};
const stages = ["pjk_review", "pjk_submitted", "supervisor_review", "supervisor_approved", "ka_bps_review", "release_ready"];

export default function ApprovalDetailPage() {
  const { id } = useParams<{ id: string }>();
  const { user } = useAuthUser();
  const [brs, setBrs] = useState<BRS | null>(null);
  const [workflow, setWorkflow] = useState<ApprovalWorkflow | null>(null);
  const [note, setNote] = useState("");
  const [busy, setBusy] = useState("");
  const [error, setError] = useState("");
  const [message, setMessage] = useState("");

  useEffect(() => {
    const token = getToken();
    if (!token) return;
    Promise.all([getBRS(token, id), getApprovalWorkflow(token, id)]).then(([brsData, workflowData]) => { setBrs(brsData); setWorkflow(workflowData); }).catch((err) => setError(err.message));
  }, [id]);

  const permissions = useMemo(() => {
    const admin = user?.user_level === "admin";
    return {
      pjk: admin || user?.id === brs?.pjk.id,
      supervisor: admin || (user?.user_level === "supervisor" && user?.id === brs?.supervisor?.id),
      kaBps: admin || user?.user_level === "ka_bps",
      submitKa: admin || user?.id === brs?.pjk.id || user?.id === brs?.supervisor?.id,
    };
  }, [user, brs]);

  async function act(name: string, request: (token: string) => Promise<ApprovalWorkflow>, success: string, requireNote = false) {
    if (requireNote && !note.trim()) { setError("Catatan wajib diisi ketika mengembalikan BRS untuk revisi."); return; }
    const token = getToken(); if (!token) return;
    setBusy(name); setError(""); setMessage("");
    try { const updated = await request(token); setWorkflow(updated); setBrs((current) => current ? { ...current, status: updated.current_status } : current); setNote(""); setMessage(success); }
    catch (err) { setError(err instanceof Error ? err.message : "Aksi persetujuan gagal."); }
    finally { setBusy(""); }
  }

  const currentIndex = stages.indexOf(workflow?.current_status || "");
  const revision = workflow?.current_status.includes("revision");

  return <AppShell title="Detail Persetujuan">
    <div className="p-6 lg:p-10">
      <Link href="/approvals" className="inline-flex items-center gap-2 text-sm font-semibold text-slate-500 hover:text-cyan-700"><ArrowLeftIcon className="h-4 w-4" />Kembali ke Pusat Persetujuan</Link>
      <div className="mt-6 rounded-2xl bg-[#102a43] p-7 text-white"><div className="flex flex-col justify-between gap-5 md:flex-row md:items-center"><div><p className="text-xs font-semibold uppercase tracking-widest text-cyan-300">{brs?.kode_brs || "Memuat..."}</p><h1 className="mt-3 text-2xl font-bold">{brs?.nama_brs || "Detail persetujuan"}</h1><p className="mt-2 text-sm text-slate-300">PJK: {brs?.pjk.nama || "—"} • Supervisor: {brs?.supervisor?.nama || "Belum ditentukan"}</p></div><span className={`w-fit rounded-full px-4 py-2 text-xs font-bold ${workflow?.current_status === "release_ready" ? "bg-emerald-400 text-emerald-950" : revision ? "bg-red-400 text-red-950" : "bg-cyan-400 text-[#102a43]"}`}>{statusLabel[workflow?.current_status || ""] || workflow?.current_status || "Memuat"}</span></div></div>
      {error && <p className="mt-5 rounded-xl bg-red-50 p-4 text-sm text-red-700">{error}</p>}
      {message && <p className="mt-5 rounded-xl bg-emerald-50 p-4 text-sm text-emerald-700">{message}</p>}

      {workflow && <>
        <section className="mt-6 grid gap-3 md:grid-cols-6">{stages.map((stage, index) => <div key={stage} className={`rounded-xl border p-3 ${index <= currentIndex && !revision ? "border-cyan-300 bg-cyan-50" : "border-slate-200 bg-white"}`}><p className="text-[10px] font-bold uppercase text-slate-400">Tahap {index + 1}</p><p className="mt-1 text-xs font-semibold text-slate-700">{statusLabel[stage]}</p></div>)}</section>

        <section className="mt-6 grid gap-4 md:grid-cols-4"><div className="rounded-2xl border border-slate-200 bg-white p-5"><p className="text-xs uppercase text-slate-400">Skor terakhir</p><p className="mt-2 text-3xl font-bold text-[#102a43]">{workflow.latest_score ? Number(workflow.latest_score).toFixed(0) : "—"}<span className="text-sm text-slate-400">/100</span></p></div><div className="rounded-2xl border border-slate-200 bg-white p-5"><p className="text-xs uppercase text-slate-400">Temuan terbuka</p><p className={`mt-2 text-3xl font-bold ${workflow.open_findings ? "text-red-600" : "text-emerald-600"}`}>{workflow.open_findings}</p></div><div className="rounded-2xl border border-slate-200 bg-white p-5"><p className="text-xs uppercase text-slate-400">Error / Warning</p><p className="mt-2 text-3xl font-bold text-slate-800">{workflow.error_count}<span className="text-slate-300"> / </span>{workflow.warning_count}</p></div><div className="flex flex-col justify-center gap-2 rounded-2xl border border-slate-200 bg-white p-5"><Link href={`/brs/${id}/checking`} className="inline-flex items-center gap-2 text-sm font-semibold text-cyan-700"><CheckBadgeIcon className="h-5 w-5" />Hasil STATCHECK</Link><Link href={`/brs/${id}/documents`} className="inline-flex items-center gap-2 text-sm font-semibold text-slate-600"><DocumentTextIcon className="h-5 w-5" />Lihat dokumen</Link></div></section>

        {revision ? <section className="mt-6 rounded-2xl border border-red-200 bg-red-50 p-6"><h2 className="font-bold text-red-800">BRS dikembalikan untuk revisi</h2><p className="mt-2 text-sm leading-6 text-red-700">Perbaiki data atau dokumen berdasarkan catatan terakhir, lalu jalankan ulang STATCHECK. Setelah semua temuan ditindaklanjuti, BRS dapat dikirim kembali dari awal alur persetujuan.</p><Link href={`/brs/${id}/checking`} className="mt-4 inline-flex items-center gap-2 rounded-xl bg-red-700 px-4 py-3 text-sm font-semibold text-white"><ArrowPathIcon className="h-5 w-5" />Perbaiki dan periksa ulang</Link></section> : ["release_ready", "released"].includes(workflow.current_status) ? <section className="mt-6 rounded-2xl border border-emerald-200 bg-emerald-50 p-7 text-center"><CheckCircleIcon className="mx-auto h-12 w-12 text-emerald-600" /><h2 className="mt-3 text-xl font-bold text-emerald-900">{workflow.current_status === "released" ? "BRS TELAH DIRILIS" : "BRS SIAP RILIS"}</h2><p className="mt-2 text-sm text-emerald-700">Seluruh tahap pemeriksaan dan persetujuan telah selesai.</p>{workflow.current_status === "release_ready" && <Link href="/releases" className="mt-4 inline-block rounded-xl bg-emerald-700 px-5 py-3 text-sm font-semibold text-white">Buka Release Center</Link>}</section> : <section className="mt-6 rounded-2xl border border-slate-200 bg-white p-6"><h2 className="font-bold text-slate-800">Keputusan dan Catatan</h2><textarea value={note} onChange={(event) => setNote(event.target.value)} rows={4} placeholder="Tambahkan catatan keputusan (wajib untuk revisi)..." className="mt-4 w-full rounded-xl border border-slate-200 p-3 text-sm outline-none focus:border-cyan-500" /><div className="mt-4 flex flex-wrap gap-3">
          {workflow.current_status === "pjk_review" && permissions.pjk && <button disabled={Boolean(busy) || workflow.open_findings > 0} onClick={() => act("submit", (token) => submitSupervisor(token, id, note), "BRS berhasil dikirim ke Supervisor.")} className="inline-flex items-center gap-2 rounded-xl bg-[#102a43] px-5 py-3 text-sm font-semibold text-white disabled:cursor-not-allowed disabled:opacity-40"><PaperAirplaneIcon className="h-5 w-5" />Kirim ke Supervisor</button>}
          {workflow.current_status === "pjk_submitted" && permissions.supervisor && <button disabled={Boolean(busy)} onClick={() => act("start", (token) => startSupervisorReview(token, id), "Pemeriksaan Supervisor dimulai.")} className="rounded-xl bg-[#102a43] px-5 py-3 text-sm font-semibold text-white">Mulai Pemeriksaan Supervisor</button>}
          {workflow.current_status === "supervisor_review" && permissions.supervisor && <><button disabled={Boolean(busy)} onClick={() => act("revision", (token) => supervisorRevision(token, id, note), "BRS dikembalikan ke PJK.", true)} className="inline-flex items-center gap-2 rounded-xl bg-red-100 px-5 py-3 text-sm font-semibold text-red-700"><XMarkIcon className="h-5 w-5" />Kembalikan</button><button disabled={Boolean(busy)} onClick={() => act("approve", (token) => supervisorApprove(token, id, note), "BRS disetujui Supervisor.")} className="inline-flex items-center gap-2 rounded-xl bg-emerald-600 px-5 py-3 text-sm font-semibold text-white"><CheckCircleIcon className="h-5 w-5" />Setujui</button></>}
          {workflow.current_status === "supervisor_approved" && permissions.submitKa && <button disabled={Boolean(busy)} onClick={() => act("submit-ka", (token) => submitKaBps(token, id, note), "BRS dikirim ke Kepala BPS.")} className="inline-flex items-center gap-2 rounded-xl bg-[#102a43] px-5 py-3 text-sm font-semibold text-white"><PaperAirplaneIcon className="h-5 w-5" />Kirim ke Kepala BPS</button>}
          {workflow.current_status === "ka_bps_review" && permissions.kaBps && <><button disabled={Boolean(busy)} onClick={() => act("ka-revision", (token) => kaBpsRevision(token, id, note), "BRS dikembalikan ke PJK.", true)} className="inline-flex items-center gap-2 rounded-xl bg-red-100 px-5 py-3 text-sm font-semibold text-red-700"><XMarkIcon className="h-5 w-5" />Kembalikan</button><button disabled={Boolean(busy)} onClick={() => act("ka-approve", (token) => kaBpsApprove(token, id, note), "BRS disetujui dan siap dirilis.")} className="inline-flex items-center gap-2 rounded-xl bg-emerald-600 px-5 py-3 text-sm font-semibold text-white"><CheckCircleIcon className="h-5 w-5" />Approve & Siap Rilis</button></>}
          {workflow.open_findings > 0 && workflow.current_status === "pjk_review" && <p className="self-center text-sm text-amber-700">Tindak lanjuti {workflow.open_findings} temuan sebelum mengirim.</p>}
        </div></section>}

        <section className="mt-6 rounded-2xl border border-slate-200 bg-white p-6"><h2 className="font-bold text-slate-800">Riwayat Persetujuan</h2><div className="mt-5 space-y-4">{[...workflow.events].reverse().map((event) => <div key={event.id} className="flex gap-4 border-l-2 border-cyan-200 pl-4"><div><p className="text-sm font-semibold text-slate-800">{actionLabel[event.action] || event.action}</p><p className="mt-1 text-xs text-slate-400">{event.user.nama} • {new Intl.DateTimeFormat("id-ID", { dateStyle: "medium", timeStyle: "short" }).format(new Date(event.created_at))}</p>{event.note && <p className="mt-2 rounded-lg bg-slate-50 p-3 text-sm text-slate-600">{event.note}</p>}</div></div>)}{!workflow.events.length && <p className="text-sm text-slate-400">Belum ada tindakan persetujuan.</p>}</div></section>
      </>}
    </div>
  </AppShell>;
}
