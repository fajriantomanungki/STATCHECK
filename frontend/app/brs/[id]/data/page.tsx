"use client";

import { ArrowLeftIcon, ArrowPathIcon, DocumentTextIcon, TrashIcon } from "@heroicons/react/24/outline";
import Link from "next/link";
import { useParams } from "next/navigation";
import { useCallback, useEffect, useState } from "react";

import { AppShell } from "@/components/app-shell";
import { getToken } from "@/lib/auth";
import { deletePresentationIndicator, getBRS, getPresentationIndicators, refreshPresentationIndicators, updatePresentationIndicator } from "@/services/api";
import type { BRS, PresentationIndicator } from "@/types/phase2";

type Draft = { analysis: string; phenomenon: string };
const dataTypeLabels: Record<string, string> = {
  percentage: "Persentase", percentage_point: "Persen poin", currency: "Mata uang",
  index: "Indeks", duration: "Durasi", count: "Jumlah", quantity: "Kuantitas",
  range: "Rentang", number: "Angka",
};
const roleLabels: Record<string, string> = { level: "Nilai", change: "Perubahan", contribution: "Kontribusi" };

export default function BRSDataPage() {
  const { id } = useParams<{ id: string }>();
  const [brs, setBrs] = useState<BRS | null>(null);
  const [items, setItems] = useState<PresentationIndicator[]>([]);
  const [drafts, setDrafts] = useState<Record<string, Draft>>({});
  const [busy, setBusy] = useState("");
  const [error, setError] = useState("");
  const [message, setMessage] = useState("");

  const applyItems = useCallback((rows: PresentationIndicator[]) => {
    setItems(rows);
    setDrafts(Object.fromEntries(rows.map((item) => [item.id, {
      analysis: item.analysis || "", phenomenon: item.phenomenon || "",
    }])));
  }, []);

  const load = useCallback(async () => {
    const token = getToken(); if (!token) return;
    const [brsResult, rows] = await Promise.all([getBRS(token, id), getPresentationIndicators(token, id)]);
    setBrs(brsResult); applyItems(rows);
  }, [applyItems, id]);

  useEffect(() => {
    const token = getToken();
    if (!token) return;
    Promise.all([getBRS(token, id), getPresentationIndicators(token, id)])
      .then(([brsResult, rows]) => { setBrs(brsResult); applyItems(rows); })
      .catch((err) => setError(err.message));
  }, [applyItems, id]);

  async function refresh() {
    const token = getToken(); if (!token) return;
    setBusy("refresh"); setError(""); setMessage("");
    try {
      applyItems(await refreshPresentationIndicators(token, id));
      setMessage("Data indikator berhasil diekstrak ulang dari Bahan Paparan dan Narasi Pimpinan aktif.");
    } catch (err) { setError(err instanceof Error ? err.message : "Ekstraksi ulang gagal."); }
    finally { setBusy(""); }
  }

  async function save(item: PresentationIndicator) {
    const token = getToken(); if (!token) return;
    const draft = drafts[item.id] || { analysis: "", phenomenon: "" };
    setBusy(item.id); setError(""); setMessage("");
    try {
      await updatePresentationIndicator(token, id, item.id, {
        analysis: draft.analysis.trim() || null, phenomenon: draft.phenomenon.trim() || null,
      });
      await load(); setMessage(`Analisis dan fenomena untuk ${item.indicator_name} tersimpan.`);
    } catch (err) { setError(err instanceof Error ? err.message : "Data gagal disimpan."); }
    finally { setBusy(""); }
  }

  async function remove(item: PresentationIndicator) {
    if (!window.confirm(`Hapus baris ${item.indicator_name} dari tabel hasil ekstraksi?`)) return;
    const token = getToken(); if (!token) return;
    try { await deletePresentationIndicator(token, id, item.id); await load(); }
    catch (err) { setError(err instanceof Error ? err.message : "Baris gagal dihapus."); }
  }

  function updateDraft(itemId: string, key: keyof Draft, value: string) {
    setDrafts((current) => ({
      ...current,
      [itemId]: { ...(current[itemId] || { analysis: "", phenomenon: "" }), [key]: value },
    }));
  }

  return <AppShell title="Data Indikator BRS"><div className="p-6 lg:p-10">
    <Link href={`/brs/${id}`} className="inline-flex items-center gap-2 text-sm font-semibold text-slate-500 hover:text-cyan-700"><ArrowLeftIcon className="h-4 w-4" />Kembali ke detail BRS</Link>
    <div className="mt-5 flex flex-col justify-between gap-5 xl:flex-row xl:items-end"><div><p className="text-sm font-semibold uppercase tracking-widest text-cyan-700">Olah BRS</p><h1 className="mt-2 text-3xl font-bold text-slate-900">Tabel Indikator Dokumen</h1><p className="mt-2 text-slate-500">{brs?.nama_brs || "Memuat BRS..."}</p><p className="mt-1 max-w-3xl text-sm text-slate-500">Nilai, wilayah, periode, tipe, dan keterangan diekstrak per kalimat dari Bahan Paparan lalu dilengkapi dari Narasi Pimpinan. Data identik tidak ditampilkan dua kali. Pengguna melengkapi kolom Analisis dan Fenomena.</p></div><div className="flex flex-wrap gap-3"><Link href={`/brs/${id}/documents`} className="inline-flex items-center gap-2 rounded-xl border border-slate-300 bg-white px-4 py-3 text-sm font-semibold text-slate-700"><DocumentTextIcon className="h-5 w-5" />Kelola Dokumen</Link><button onClick={refresh} disabled={Boolean(busy)} className="inline-flex items-center gap-2 rounded-xl bg-[#102a43] px-4 py-3 text-sm font-semibold text-white disabled:opacity-50"><ArrowPathIcon className={`h-5 w-5 ${busy === "refresh" ? "animate-spin" : ""}`} />Ekstrak Ulang</button></div></div>
    {error && <p className="mt-5 rounded-xl bg-red-50 p-4 text-sm text-red-700">{error}</p>}{message && <p className="mt-5 rounded-xl bg-emerald-50 p-4 text-sm text-emerald-700">{message}</p>}

    <div className="mt-7 overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-sm"><div className="flex items-center justify-between border-b border-slate-200 px-6 py-5"><div><h2 className="font-bold text-slate-800">Hasil Ekstraksi Aktif</h2><p className="mt-1 text-xs text-slate-400">Sumber: Bahan Paparan dan Narasi Pimpinan versi aktif</p></div><span className="rounded-full bg-cyan-50 px-3 py-1 text-sm font-semibold text-cyan-700">{items.length} baris</span></div><div className="overflow-x-auto"><table className="w-full min-w-[1500px] text-left text-sm"><thead className="bg-slate-50 text-xs uppercase tracking-wide text-slate-500"><tr><th className="px-4 py-4">Indikator</th><th className="px-4 py-4">Nilai</th><th className="px-4 py-4">Periode</th><th className="px-4 py-4">Tipe Data</th><th className="px-4 py-4">Metadata / Penjelasan</th><th className="w-72 px-4 py-4">Analisis</th><th className="w-72 px-4 py-4">Fenomena</th><th className="px-4 py-4">Aksi</th></tr></thead><tbody className="divide-y divide-slate-100">
      {items.map((item) => <tr key={item.id} className="align-top"><td className="px-4 py-4"><p className="font-semibold text-slate-800">{item.indicator_name}</p><p className="mt-1 text-xs font-semibold text-cyan-700">{item.source_document_type === "bahan_paparan" ? "Bahan Paparan" : "Narasi Pimpinan"}</p><p className="mt-1 text-xs text-slate-400">{item.source_document_type === "bahan_paparan" ? "Slide" : "Halaman"} {item.page_number}{item.comparison_basis ? ` • ${item.comparison_basis}` : ""} • {roleLabels[item.value_role] || item.value_role}</p></td><td className="px-4 py-4"><p className="text-lg font-bold text-[#102a43]">{item.value_text}</p><p className="text-xs text-slate-400">{item.unit || "tanpa satuan"}</p></td><td className="px-4 py-4 text-slate-600">{item.period_label || "Tidak terdeteksi"}</td><td className="px-4 py-4"><span className="rounded-full bg-violet-50 px-2.5 py-1 text-xs font-semibold text-violet-700">{dataTypeLabels[item.data_type] || item.data_type}</span></td><td className="max-w-md px-4 py-4 text-xs leading-5 text-slate-600"><p className="max-h-32 overflow-y-auto">{item.metadata_text}</p></td><td className="px-4 py-4"><textarea rows={5} value={drafts[item.id]?.analysis || ""} onChange={(e) => updateDraft(item.id, "analysis", e.target.value)} className="w-full resize-y rounded-lg border border-slate-300 px-3 py-2 text-sm outline-none focus:border-cyan-600" placeholder="Uraikan perubahan dan makna data..." /></td><td className="px-4 py-4"><textarea rows={5} value={drafts[item.id]?.phenomenon || ""} onChange={(e) => updateDraft(item.id, "phenomenon", e.target.value)} className="w-full resize-y rounded-lg border border-slate-300 px-3 py-2 text-sm outline-none focus:border-cyan-600" placeholder="Tuliskan fenomena pendukung..." /></td><td className="px-4 py-4"><div className="flex flex-col gap-2"><button onClick={() => save(item)} disabled={Boolean(busy)} className="rounded-lg bg-cyan-700 px-3 py-2 text-xs font-semibold text-white disabled:opacity-50">{busy === item.id ? "Menyimpan..." : "Simpan"}</button><button onClick={() => remove(item)} title="Hapus baris" className="inline-flex items-center justify-center gap-1 rounded-lg bg-red-50 px-3 py-2 text-xs font-semibold text-red-600"><TrashIcon className="h-4 w-4" />Hapus</button></div></td></tr>)}
      {!items.length && <tr><td colSpan={8} className="px-6 py-16 text-center"><DocumentTextIcon className="mx-auto h-10 w-10 text-slate-300" /><p className="mt-3 font-semibold text-slate-600">Belum ada indikator hasil ekstraksi.</p><p className="mt-1 text-sm text-slate-400">Unggah Bahan Paparan atau Narasi Pimpinan pada menu Kelola Dokumen, lalu kembali ke halaman ini.</p></td></tr>}
    </tbody></table></div></div>
  </div></AppShell>;
}
