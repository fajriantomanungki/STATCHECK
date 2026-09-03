"use client";

import { ArrowDownTrayIcon, ArrowLeftIcon, DocumentArrowDownIcon, DocumentTextIcon } from "@heroicons/react/24/outline";
import Link from "next/link";
import { useParams } from "next/navigation";
import { useEffect, useState } from "react";

import { AppShell } from "@/components/app-shell";
import { useAuthUser } from "@/hooks/use-auth-user";
import { getToken } from "@/lib/auth";
import { downloadMinutes, generateMinutes, getMinutes, getRelease, updateMinutes } from "@/services/api";
import type { ReleaseDetail } from "@/types/phase6";
import type { Minutes, MinutesForm } from "@/types/phase7";

const emptyForm: MinutesForm = { opening: null, discussion: null, notes: null, conclusion: null };

export default function MinutesPage() {
  const { id } = useParams<{ id: string }>();
  const { user } = useAuthUser();
  const [release, setRelease] = useState<ReleaseDetail | null>(null);
  const [minutes, setMinutes] = useState<Minutes | null>(null);
  const [form, setForm] = useState<MinutesForm>(emptyForm);
  const [busy, setBusy] = useState("");
  const [error, setError] = useState("");
  const [message, setMessage] = useState("");
  useEffect(() => {
    const token = getToken(); if (!token) return;
    Promise.all([getRelease(token, id), getMinutes(token, id)]).then(([releaseData, minutesData]) => {
      setRelease(releaseData); setMinutes(minutesData);
      if (minutesData) setForm({ opening: minutesData.opening, discussion: minutesData.discussion, notes: minutesData.notes, conclusion: minutesData.conclusion });
    }).catch((err) => setError(err.message));
  }, [id]);

  const canManage = (user?.user_level === "admin" || user?.user_level === "humas") && release?.status !== "draft";
  async function save() {
    const token = getToken(); if (!token) return null;
    setBusy("save"); setError(""); setMessage("");
    try { const saved = await updateMinutes(token, id, form); setMinutes(saved); setMessage("Isi notulen berhasil disimpan."); return saved; }
    catch (err) { setError(err instanceof Error ? err.message : "Notulen gagal disimpan."); return null; }
    finally { setBusy(""); }
  }
  async function generate() {
    const token = getToken(); if (!token) return;
    setBusy("generate"); setError(""); setMessage("");
    try { await updateMinutes(token, id, form); const generated = await generateMinutes(token, id); setMinutes(generated); setMessage("Notulen DOCX dan PDF berhasil dibuat."); }
    catch (err) { setError(err instanceof Error ? err.message : "File notulen gagal dibuat."); }
    finally { setBusy(""); }
  }
  async function download(format: "docx" | "pdf") {
    const token = getToken(); if (!token) return;
    setBusy(format); setError("");
    try { await downloadMinutes(token, id, format); }
    catch (err) { setError(err instanceof Error ? err.message : "File gagal diunduh."); }
    finally { setBusy(""); }
  }

  return <AppShell title="Notulen Rilis"><div className="p-6 lg:p-10">
    <Link href={`/releases/${id}`} className="inline-flex items-center gap-2 text-sm font-semibold text-slate-500 hover:text-cyan-700"><ArrowLeftIcon className="h-4 w-4" />Kembali ke detail rilis</Link>
    <div className="mt-6"><p className="text-sm font-semibold uppercase tracking-widest text-cyan-700">Phase 7</p><h1 className="mt-2 text-3xl font-bold text-slate-900">Notulen Rilis</h1><p className="mt-2 text-slate-500">{release?.judul_rilis || "Memuat kegiatan..."}</p></div>
    {error && <p className="mt-5 rounded-xl bg-red-50 p-4 text-sm text-red-700">{error}</p>}{message && <p className="mt-5 rounded-xl bg-emerald-50 p-4 text-sm text-emerald-700">{message}</p>}
    {release?.status === "draft" && <p className="mt-5 rounded-xl bg-amber-50 p-4 text-sm text-amber-800">Notulen dapat diisi setelah kegiatan rilis dimulai.</p>}
    <div className="mt-7 grid gap-6 xl:grid-cols-[1fr_1fr]">
      <section className="rounded-2xl border border-slate-200 bg-white p-6"><div className="flex items-center gap-3"><DocumentTextIcon className="h-7 w-7 text-cyan-700" /><div><h2 className="font-bold text-slate-800">Lembar Kerja Humas</h2><p className="text-sm text-slate-500">Peserta, daftar BRS, dan Q&A final ditambahkan otomatis.</p></div></div><div className="mt-5 space-y-4"><label className="block text-sm font-semibold text-slate-700">Pembukaan<textarea disabled={!canManage} value={form.opening || ""} onChange={(e) => setForm({ ...form, opening: e.target.value || null })} rows={4} className="mt-2 w-full rounded-xl border border-slate-200 p-3 font-normal outline-none focus:border-cyan-500 disabled:bg-slate-50" /></label><label className="block text-sm font-semibold text-slate-700">Pokok Pembahasan<textarea disabled={!canManage} value={form.discussion || ""} onChange={(e) => setForm({ ...form, discussion: e.target.value || null })} rows={5} className="mt-2 w-full rounded-xl border border-slate-200 p-3 font-normal outline-none focus:border-cyan-500 disabled:bg-slate-50" /></label><label className="block text-sm font-semibold text-slate-700">Catatan<textarea disabled={!canManage} value={form.notes || ""} onChange={(e) => setForm({ ...form, notes: e.target.value || null })} rows={4} className="mt-2 w-full rounded-xl border border-slate-200 p-3 font-normal outline-none focus:border-cyan-500 disabled:bg-slate-50" /></label><label className="block text-sm font-semibold text-slate-700">Kesimpulan<textarea disabled={!canManage} value={form.conclusion || ""} onChange={(e) => setForm({ ...form, conclusion: e.target.value || null })} rows={4} className="mt-2 w-full rounded-xl border border-slate-200 p-3 font-normal outline-none focus:border-cyan-500 disabled:bg-slate-50" /></label></div>{canManage && <div className="mt-5 flex flex-wrap gap-3"><button disabled={Boolean(busy)} onClick={save} className="rounded-xl bg-slate-200 px-5 py-3 text-sm font-semibold text-slate-700 disabled:opacity-40">{busy === "save" ? "Menyimpan..." : "Simpan Draft"}</button><button disabled={Boolean(busy)} onClick={generate} className="inline-flex items-center gap-2 rounded-xl bg-[#102a43] px-5 py-3 text-sm font-semibold text-white disabled:opacity-40"><DocumentArrowDownIcon className="h-5 w-5" />{busy === "generate" ? "Membuat file..." : "Generate DOCX & PDF"}</button></div>}</section>
      <section className="rounded-2xl border border-slate-200 bg-white p-6"><h2 className="font-bold text-slate-800">Preview Notulen Terakhir</h2>{minutes?.content ? <pre className="mt-5 max-h-[720px] overflow-auto whitespace-pre-wrap rounded-xl bg-slate-50 p-5 font-sans text-sm leading-6 text-slate-700">{minutes.content}</pre> : <div className="mt-5 grid min-h-64 place-items-center rounded-xl border border-dashed border-slate-300 text-center text-sm text-slate-400">Belum ada file notulen yang dihasilkan.</div>}<div className="mt-5 flex flex-wrap gap-3"><button disabled={!minutes?.docx_ready || Boolean(busy)} onClick={() => download("docx")} className="inline-flex items-center gap-2 rounded-xl bg-blue-600 px-4 py-3 text-sm font-semibold text-white disabled:opacity-40"><ArrowDownTrayIcon className="h-5 w-5" />Unduh DOCX</button><button disabled={!minutes?.pdf_ready || Boolean(busy)} onClick={() => download("pdf")} className="inline-flex items-center gap-2 rounded-xl bg-red-600 px-4 py-3 text-sm font-semibold text-white disabled:opacity-40"><ArrowDownTrayIcon className="h-5 w-5" />Unduh PDF</button></div></section>
    </div>
  </div></AppShell>;
}

