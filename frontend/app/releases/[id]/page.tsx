"use client";

import { ArrowLeftIcon, CheckCircleIcon, ClockIcon, DocumentTextIcon, PauseCircleIcon, PlayCircleIcon, PlusIcon, TrashIcon, UserGroupIcon } from "@heroicons/react/24/outline";
import Link from "next/link";
import { useParams, useRouter } from "next/navigation";
import { useEffect, useState } from "react";

import { AppShell } from "@/components/app-shell";
import { useAuthUser } from "@/hooks/use-auth-user";
import { getToken } from "@/lib/auth";
import { addReleaseBRS, completeRelease, deleteRelease, getEligibleBRS, getRelease, removeReleaseBRS, startRelease } from "@/services/api";
import type { ReleaseBRS, ReleaseDetail } from "@/types/phase6";

const statusLabel = { draft: "Persiapan", ongoing: "Sedang Berlangsung", completed: "Selesai" };

export default function ReleaseDetailPage() {
  const { id } = useParams<{ id: string }>();
  const router = useRouter();
  const { user } = useAuthUser();
  const [release, setRelease] = useState<ReleaseDetail | null>(null);
  const [eligible, setEligible] = useState<ReleaseBRS[]>([]);
  const [busy, setBusy] = useState("");
  const [error, setError] = useState("");
  const [message, setMessage] = useState("");
  const canManage = user?.user_level === "admin" || user?.user_level === "humas";

  function load() {
    const token = getToken(); if (!token) return;
    getRelease(token, id).then((data) => { setRelease(data); if (data.status === "draft") getEligibleBRS(token, data.tanggal_rilis).then(setEligible).catch(() => setEligible([])); }).catch((err) => setError(err.message));
  }
  useEffect(load, [id]);

  async function act(name: string, request: (token: string) => Promise<ReleaseDetail>, success: string) {
    const token = getToken(); if (!token) return;
    setBusy(name); setError(""); setMessage("");
    try { const updated = await request(token); setRelease(updated); setMessage(success); if (updated.status === "draft") getEligibleBRS(token, updated.tanggal_rilis).then(setEligible); }
    catch (err) { setError(err instanceof Error ? err.message : "Aksi Release Center gagal."); }
    finally { setBusy(""); }
  }
  async function remove() {
    if (!window.confirm("Hapus kegiatan rilis ini? BRS akan kembali tersedia untuk kegiatan lain.")) return;
    const token = getToken(); if (!token) return;
    setBusy("delete");
    try { await deleteRelease(token, id); router.push("/releases"); }
    catch (err) { setError(err instanceof Error ? err.message : "Kegiatan gagal dihapus."); setBusy(""); }
  }

  return <AppShell title="Detail Kegiatan Rilis"><div className="p-6 lg:p-10">
    <Link href="/releases" className="inline-flex items-center gap-2 text-sm font-semibold text-slate-500 hover:text-cyan-700"><ArrowLeftIcon className="h-4 w-4" />Kembali ke Release Center</Link>
    {!release ? <p className="mt-10 text-sm text-slate-400">Memuat kegiatan rilis...</p> : <>
      <section className="mt-6 rounded-2xl bg-[#102a43] p-7 text-white"><div className="flex flex-col justify-between gap-5 lg:flex-row lg:items-center"><div><p className="text-xs font-bold uppercase tracking-widest text-cyan-300">{release.kode_rilis}</p><h1 className="mt-3 text-3xl font-bold">{release.judul_rilis}</h1><p className="mt-3 text-sm text-slate-300">{new Intl.DateTimeFormat("id-ID", { dateStyle: "full" }).format(new Date(`${release.tanggal_rilis}T00:00:00`))} • {release.waktu_rilis.slice(0, 5)} • {release.tempat}</p></div><span className={`w-fit rounded-full px-4 py-2 text-xs font-bold ${release.status === "completed" ? "bg-emerald-400 text-emerald-950" : release.status === "ongoing" ? "bg-cyan-400 text-[#102a43]" : "bg-amber-300 text-amber-950"}`}>{statusLabel[release.status]}</span></div></section>
      {error && <p className="mt-5 rounded-xl bg-red-50 p-4 text-sm text-red-700">{error}</p>}{message && <p className="mt-5 rounded-xl bg-emerald-50 p-4 text-sm text-emerald-700">{message}</p>}

      <section className="mt-6 grid gap-4 md:grid-cols-3"><div className="rounded-2xl border border-slate-200 bg-white p-5"><DocumentTextIcon className="h-7 w-7 text-cyan-700" /><p className="mt-4 text-3xl font-bold text-[#102a43]">{release.jumlah_brs}</p><p className="text-sm text-slate-500">BRS dalam kegiatan</p></div><div className="rounded-2xl border border-slate-200 bg-white p-5"><UserGroupIcon className="h-7 w-7 text-cyan-700" /><p className="mt-4 text-3xl font-bold text-[#102a43]">{release.jumlah_tamu}</p><p className="text-sm text-slate-500">Peserta terdaftar</p></div><div className="flex flex-col justify-center rounded-2xl border border-slate-200 bg-white p-5"><p className="text-xs uppercase text-slate-400">Dibuat oleh</p><p className="mt-2 font-semibold text-slate-800">{release.creator.nama}</p><p className="mt-1 text-sm text-slate-500">{release.creator.fungsi}</p></div></section>

      {canManage && <section className="mt-6 flex flex-wrap gap-3 rounded-2xl border border-slate-200 bg-white p-5">{release.status === "draft" && <><button disabled={Boolean(busy) || !release.brs.length} onClick={() => act("start", (token) => startRelease(token, id), "Kegiatan rilis telah dimulai.")} className="inline-flex items-center gap-2 rounded-xl bg-cyan-600 px-5 py-3 text-sm font-semibold text-white disabled:opacity-40"><PlayCircleIcon className="h-5 w-5" />Mulai Kegiatan</button><button disabled={Boolean(busy)} onClick={remove} className="inline-flex items-center gap-2 rounded-xl bg-red-50 px-5 py-3 text-sm font-semibold text-red-700"><TrashIcon className="h-5 w-5" />Hapus Kegiatan</button></>}{release.status === "ongoing" && <button disabled={Boolean(busy)} onClick={() => act("complete", (token) => completeRelease(token, id), "Kegiatan selesai dan seluruh BRS berstatus Telah Dirilis.")} className="inline-flex items-center gap-2 rounded-xl bg-emerald-600 px-5 py-3 text-sm font-semibold text-white"><CheckCircleIcon className="h-5 w-5" />Selesaikan Rilis</button>}{release.status === "completed" && <p className="inline-flex items-center gap-2 text-sm font-semibold text-emerald-700"><CheckCircleIcon className="h-5 w-5" />Kegiatan telah selesai dan dikunci.</p>}</section>}

      <section className="mt-6 rounded-2xl border border-slate-200 bg-white p-6"><div className="flex flex-col justify-between gap-3 sm:flex-row sm:items-center"><div><h2 className="font-bold text-slate-800">Berita Resmi Statistik</h2><p className="mt-1 text-sm text-slate-500">BRS yang dipublikasikan dalam kegiatan ini.</p></div></div><div className="mt-5 space-y-3">{release.brs.map((brs) => <div key={brs.id} className="flex flex-col justify-between gap-3 rounded-xl bg-slate-50 p-4 sm:flex-row sm:items-center"><div><Link href={`/brs/${brs.id}`} className="font-semibold text-[#102a43] hover:text-cyan-700">{brs.nama_brs}</Link><p className="mt-1 text-xs text-slate-400">{brs.kode_brs} • {brs.fungsi_pj}</p></div>{canManage && release.status === "draft" && <button onClick={() => act(`remove-${brs.id}`, (token) => removeReleaseBRS(token, id, brs.id), "BRS dikeluarkan dari kegiatan.")} className="text-xs font-semibold text-red-600">Keluarkan</button>}</div>)}{!release.brs.length && <p className="text-sm text-slate-400">Belum ada BRS dalam kegiatan.</p>}</div>{canManage && release.status === "draft" && eligible.length > 0 && <div className="mt-5 border-t border-slate-100 pt-5"><p className="text-sm font-semibold text-slate-700">Tambahkan BRS siap rilis</p><div className="mt-3 flex flex-wrap gap-2">{eligible.map((brs) => <button key={brs.id} disabled={Boolean(busy)} onClick={() => act(`add-${brs.id}`, (token) => addReleaseBRS(token, id, brs.id), "BRS ditambahkan ke kegiatan.")} className="inline-flex items-center gap-2 rounded-lg border border-cyan-200 bg-cyan-50 px-3 py-2 text-xs font-semibold text-cyan-800"><PlusIcon className="h-4 w-4" />{brs.nama_brs}</button>)}</div></div>}</section>

      <section className="mt-6 grid gap-4 md:grid-cols-3"><Link href={`/releases/${id}/guests`} className="rounded-2xl border border-slate-200 bg-white p-6 transition hover:border-cyan-400"><UserGroupIcon className="h-7 w-7 text-cyan-700" /><h2 className="mt-4 font-bold text-slate-800">Daftar Undangan</h2><p className="mt-2 text-sm text-slate-500">Kelola nama, instansi, jabatan, kontak, dan email peserta.</p></Link><div className="rounded-2xl border border-dashed border-slate-300 bg-slate-50 p-6 text-slate-400"><PauseCircleIcon className="h-7 w-7" /><h2 className="mt-4 font-bold">Sesi Q&A</h2><p className="mt-2 text-sm">Fondasi database tersedia. Antarmuka diaktifkan pada Phase 7.</p></div><div className="rounded-2xl border border-dashed border-slate-300 bg-slate-50 p-6 text-slate-400"><ClockIcon className="h-7 w-7" /><h2 className="mt-4 font-bold">Notulen Rilis</h2><p className="mt-2 text-sm">Fondasi database tersedia. Generator diaktifkan pada Phase 7.</p></div></section>
    </>}
  </div></AppShell>;
}

