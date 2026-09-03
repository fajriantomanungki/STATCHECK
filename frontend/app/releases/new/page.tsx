"use client";

import { ArrowLeftIcon, CalendarDaysIcon, CheckCircleIcon } from "@heroicons/react/24/outline";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { FormEvent, useEffect, useState } from "react";

import { AppShell } from "@/components/app-shell";
import { getToken } from "@/lib/auth";
import { createRelease, getEligibleBRS } from "@/services/api";
import type { ReleaseBRS, ReleaseForm } from "@/types/phase6";

const initialForm: ReleaseForm = { tanggal_rilis: "", waktu_rilis: "09:00", tempat: "", judul_rilis: "", brs_ids: [] };

export default function NewReleasePage() {
  const router = useRouter();
  const [form, setForm] = useState(initialForm);
  const [eligible, setEligible] = useState<ReleaseBRS[]>([]);
  const [loadingBRS, setLoadingBRS] = useState(false);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    const token = getToken();
    if (!token || !form.tanggal_rilis) return;
    getEligibleBRS(token, form.tanggal_rilis).then(setEligible).catch((err) => setError(err.message)).finally(() => setLoadingBRS(false));
  }, [form.tanggal_rilis]);

  function toggle(id: string) { setForm((current) => ({ ...current, brs_ids: current.brs_ids.includes(id) ? current.brs_ids.filter((item) => item !== id) : [...current.brs_ids, id] })); }
  async function submit(event: FormEvent) {
    event.preventDefault(); const token = getToken(); if (!token) return;
    setBusy(true); setError("");
    try { const created = await createRelease(token, form); router.push(`/releases/${created.id}`); }
    catch (err) { setError(err instanceof Error ? err.message : "Kegiatan rilis gagal dibuat."); }
    finally { setBusy(false); }
  }

  return <AppShell title="Buat Kegiatan Rilis"><div className="p-6 lg:p-10">
    <Link href="/releases" className="inline-flex items-center gap-2 text-sm font-semibold text-slate-500 hover:text-cyan-700"><ArrowLeftIcon className="h-4 w-4" />Kembali ke Release Center</Link>
    <div className="mt-6"><p className="text-sm font-semibold uppercase tracking-widest text-cyan-700">Phase 6</p><h1 className="mt-2 text-3xl font-bold text-slate-900">Registrasi Kegiatan Rilis</h1><p className="mt-2 text-slate-500">Pilih tanggal terlebih dahulu untuk menampilkan BRS yang siap dirilis.</p></div>
    {error && <p className="mt-5 rounded-xl bg-red-50 p-4 text-sm text-red-700">{error}</p>}
    <form onSubmit={submit} className="mt-7 grid gap-6 xl:grid-cols-[1fr_1.2fr]">
      <section className="rounded-2xl border border-slate-200 bg-white p-6"><h2 className="font-bold text-slate-800">Informasi Rilis</h2><div className="mt-5 grid gap-4 sm:grid-cols-2"><label className="text-sm font-semibold text-slate-700">Tanggal Rilis<input required type="date" value={form.tanggal_rilis} onChange={(e) => { const value = e.target.value; setForm({ ...form, tanggal_rilis: value, brs_ids: [] }); setEligible([]); setLoadingBRS(Boolean(value)); setError(""); }} className="mt-2 w-full rounded-xl border border-slate-200 px-4 py-3 font-normal outline-none focus:border-cyan-500" /></label><label className="text-sm font-semibold text-slate-700">Waktu<input required type="time" value={form.waktu_rilis} onChange={(e) => setForm({ ...form, waktu_rilis: e.target.value })} className="mt-2 w-full rounded-xl border border-slate-200 px-4 py-3 font-normal outline-none focus:border-cyan-500" /></label></div><label className="mt-4 block text-sm font-semibold text-slate-700">Judul Rilis<input required value={form.judul_rilis} onChange={(e) => setForm({ ...form, judul_rilis: e.target.value })} placeholder="Rilis Berita Resmi Statistik September 2026" className="mt-2 w-full rounded-xl border border-slate-200 px-4 py-3 font-normal outline-none focus:border-cyan-500" /></label><label className="mt-4 block text-sm font-semibold text-slate-700">Tempat<input required value={form.tempat} onChange={(e) => setForm({ ...form, tempat: e.target.value })} placeholder="Aula BPS Provinsi Sulawesi Tengah" className="mt-2 w-full rounded-xl border border-slate-200 px-4 py-3 font-normal outline-none focus:border-cyan-500" /></label></section>
      <section className="rounded-2xl border border-slate-200 bg-white p-6"><div className="flex items-center gap-3"><CalendarDaysIcon className="h-6 w-6 text-cyan-700" /><div><h2 className="font-bold text-slate-800">BRS Siap Rilis</h2><p className="text-sm text-slate-500">Hanya BRS dengan tanggal sama dan status Siap Rilis.</p></div></div><div className="mt-5 space-y-3">{loadingBRS && <p className="text-sm text-slate-400">Memuat BRS...</p>}{eligible.map((brs) => <label key={brs.id} className={`flex cursor-pointer items-start gap-3 rounded-xl border p-4 ${form.brs_ids.includes(brs.id) ? "border-cyan-400 bg-cyan-50" : "border-slate-200"}`}><input type="checkbox" checked={form.brs_ids.includes(brs.id)} onChange={() => toggle(brs.id)} className="mt-1 h-4 w-4 accent-cyan-700" /><div><p className="font-semibold text-slate-800">{brs.nama_brs}</p><p className="mt-1 text-xs text-slate-400">{brs.kode_brs} • {brs.fungsi_pj}</p></div></label>)}{form.tanggal_rilis && !loadingBRS && !eligible.length && <p className="rounded-xl bg-amber-50 p-4 text-sm text-amber-700">Belum ada BRS berstatus Siap Rilis pada tanggal ini.</p>}{!form.tanggal_rilis && <p className="rounded-xl bg-slate-50 p-4 text-sm text-slate-500">Silakan pilih tanggal rilis.</p>}</div></section>
      <div className="xl:col-span-2 flex justify-end"><button disabled={busy || !form.brs_ids.length} className="inline-flex items-center gap-2 rounded-xl bg-[#102a43] px-6 py-3 font-semibold text-white disabled:cursor-not-allowed disabled:opacity-40"><CheckCircleIcon className="h-5 w-5" />{busy ? "Menyimpan..." : "Buat Kegiatan Rilis"}</button></div>
    </form>
  </div></AppShell>;
}
