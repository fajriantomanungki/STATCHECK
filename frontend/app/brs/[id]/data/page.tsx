"use client";

import { ArrowLeftIcon, PencilIcon, PlusIcon, TrashIcon, XMarkIcon } from "@heroicons/react/24/outline";
import Link from "next/link";
import { useParams } from "next/navigation";
import { FormEvent, useCallback, useEffect, useState } from "react";

import { AppShell } from "@/components/app-shell";
import { getToken } from "@/lib/auth";
import { createBRSData, deleteBRSData, getBRS, getBRSData, getIndicators, updateBRSData } from "@/services/api";
import type { BRS, BRSData, BRSDataForm, Indicator } from "@/types/phase2";

const emptyForm: BRSDataForm = { indicator_id: "", sub_indikator: "", periode_data: "", deskripsi_periode: "", nilai_data: "", satuan: "", analisis: "", fenomena: "" };

export default function BRSDataPage() {
  const { id } = useParams<{ id: string }>();
  const [brs, setBrs] = useState<BRS | null>(null);
  const [indicators, setIndicators] = useState<Indicator[]>([]);
  const [items, setItems] = useState<BRSData[]>([]);
  const [form, setForm] = useState<BRSDataForm>(emptyForm);
  const [editingId, setEditingId] = useState<string | null>(null);
  const [error, setError] = useState("");
  const [saving, setSaving] = useState(false);

  const load = useCallback(async () => {
    const token = getToken(); if (!token) return;
    const [brsResult, indicatorResult, dataResult] = await Promise.all([getBRS(token, id), getIndicators(token, true), getBRSData(token, id)]);
    setBrs(brsResult); setIndicators(indicatorResult); setItems(dataResult);
  }, [id]);
  useEffect(() => {
    const token = getToken();
    if (!token) return;
    Promise.all([getBRS(token, id), getIndicators(token, true), getBRSData(token, id)])
      .then(([brsResult, indicatorResult, dataResult]) => {
        setBrs(brsResult); setIndicators(indicatorResult); setItems(dataResult);
      })
      .catch((err) => setError(err.message));
  }, [id]);

  function selectIndicator(indicatorId: string) {
    const indicator = indicators.find((item) => item.id === indicatorId);
    setForm({ ...form, indicator_id: indicatorId, satuan: indicator?.satuan_default || form.satuan });
  }

  function edit(item: BRSData) {
    setEditingId(item.id);
    setForm({ indicator_id: item.indicator_id, sub_indikator: item.sub_indikator || "", periode_data: item.periode_data, deskripsi_periode: item.deskripsi_periode, nilai_data: item.nilai_data, satuan: item.satuan, analisis: item.analisis || "", fenomena: item.fenomena || "" });
    window.scrollTo({ top: 0, behavior: "smooth" });
  }

  function cancelEdit() { setEditingId(null); setForm(emptyForm); setError(""); }

  async function submit(event: FormEvent) {
    event.preventDefault(); setSaving(true); setError("");
    try {
      const token = getToken(); if (!token) return;
      if (editingId) await updateBRSData(token, id, editingId, form);
      else await createBRSData(token, id, form);
      cancelEdit(); await load();
    } catch (err) { setError(err instanceof Error ? err.message : "Data gagal disimpan."); }
    finally { setSaving(false); }
  }

  async function remove(dataId: string) {
    if (!window.confirm("Hapus data indikator ini?")) return;
    const token = getToken(); if (!token) return;
    try { await deleteBRSData(token, id, dataId); await load(); }
    catch (err) { setError(err instanceof Error ? err.message : "Data gagal dihapus."); }
  }

  return (
    <AppShell title="Data BRS">
      <div className="p-6 lg:p-10">
        <Link href={`/brs/${id}`} className="inline-flex items-center gap-2 text-sm font-semibold text-slate-500 hover:text-cyan-700"><ArrowLeftIcon className="h-4 w-4" />Kembali ke detail BRS</Link>
        <div className="mt-5"><p className="text-sm font-semibold uppercase tracking-widest text-cyan-700">Input Data BRS</p><h1 className="mt-2 text-3xl font-bold text-slate-900">{brs?.nama_brs || "Memuat BRS..."}</h1><p className="mt-2 text-slate-500">Masukkan nilai, analisis, dan fenomena untuk setiap indikator.</p></div>

        <form onSubmit={submit} className="mt-7 rounded-2xl border border-slate-200 bg-white p-6 shadow-sm lg:p-8">
          <div className="flex items-center justify-between"><h2 className="flex items-center gap-2 font-bold text-slate-800">{editingId ? <PencilIcon className="h-5 w-5 text-cyan-700" /> : <PlusIcon className="h-5 w-5 text-cyan-700" />}{editingId ? "Edit Data Indikator" : "Tambah Data Indikator"}</h2>{editingId && <button type="button" onClick={cancelEdit} className="flex items-center gap-1 text-xs font-semibold text-slate-500"><XMarkIcon className="h-4 w-4" />Batal edit</button>}</div>
          <div className="mt-5 grid gap-5 md:grid-cols-2 xl:grid-cols-4">
            <label className="block text-sm font-medium text-slate-700 xl:col-span-2">Indikator<select required value={form.indicator_id} onChange={(e) => selectIndicator(e.target.value)} className="mt-2 w-full rounded-xl border border-slate-300 bg-white px-4 py-3 outline-none focus:border-cyan-600"><option value="">Pilih indikator</option>{indicators.map((item) => <option key={item.id} value={item.id}>{item.nama_indikator} — {item.kategori}</option>)}</select></label>
            <label className="block text-sm font-medium text-slate-700 xl:col-span-2">Subindikator<input value={form.sub_indikator || ""} onChange={(e) => setForm({ ...form, sub_indikator: e.target.value })} className="mt-2 w-full rounded-xl border border-slate-300 px-4 py-3 outline-none focus:border-cyan-600" placeholder="Contoh: Hotel Bintang" /></label>
            <label className="block text-sm font-medium text-slate-700">Periode data<input type="date" required value={form.periode_data} onChange={(e) => setForm({ ...form, periode_data: e.target.value })} className="mt-2 w-full rounded-xl border border-slate-300 px-4 py-3 outline-none focus:border-cyan-600" /></label>
            <label className="block text-sm font-medium text-slate-700">Deskripsi periode<input required value={form.deskripsi_periode} onChange={(e) => setForm({ ...form, deskripsi_periode: e.target.value })} className="mt-2 w-full rounded-xl border border-slate-300 px-4 py-3 outline-none focus:border-cyan-600" placeholder="Juli 2026" /></label>
            <label className="block text-sm font-medium text-slate-700">Nilai<input type="number" step="any" required value={form.nilai_data} onChange={(e) => setForm({ ...form, nilai_data: e.target.value })} className="mt-2 w-full rounded-xl border border-slate-300 px-4 py-3 outline-none focus:border-cyan-600" placeholder="51.95" /></label>
            <label className="block text-sm font-medium text-slate-700">Satuan<input required value={form.satuan} onChange={(e) => setForm({ ...form, satuan: e.target.value })} className="mt-2 w-full rounded-xl border border-slate-300 px-4 py-3 outline-none focus:border-cyan-600" placeholder="persen" /></label>
            <label className="block text-sm font-medium text-slate-700 md:col-span-2">Analisis<textarea rows={4} value={form.analisis || ""} onChange={(e) => setForm({ ...form, analisis: e.target.value })} className="mt-2 w-full resize-y rounded-xl border border-slate-300 px-4 py-3 outline-none focus:border-cyan-600" placeholder="Uraikan perubahan dibandingkan periode sebelumnya..." /></label>
            <label className="block text-sm font-medium text-slate-700 md:col-span-2">Fenomena<textarea rows={4} value={form.fenomena || ""} onChange={(e) => setForm({ ...form, fenomena: e.target.value })} className="mt-2 w-full resize-y rounded-xl border border-slate-300 px-4 py-3 outline-none focus:border-cyan-600" placeholder="Tuliskan fenomena pendukung indikator..." /></label>
          </div>
          {error && <p className="mt-5 rounded-lg bg-red-50 p-3 text-sm text-red-700">{error}</p>}
          <div className="mt-6 flex justify-end"><button disabled={saving} className="rounded-xl bg-[#102a43] px-6 py-3 font-semibold text-white disabled:opacity-50">{saving ? "Menyimpan..." : editingId ? "Simpan Perubahan" : "Tambah Data"}</button></div>
        </form>

        <div className="mt-7 overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-sm"><div className="flex items-center justify-between border-b border-slate-200 px-6 py-5"><h2 className="font-bold text-slate-800">Data Indikator Tersimpan</h2><span className="text-sm text-slate-400">{items.length} data</span></div><div className="overflow-x-auto"><table className="w-full text-left text-sm"><thead className="bg-slate-50 text-xs uppercase tracking-wide text-slate-500"><tr><th className="px-6 py-4">Indikator</th><th className="px-6 py-4">Periode</th><th className="px-6 py-4 text-right">Nilai</th><th className="px-6 py-4">Analisis & Fenomena</th><th className="px-6 py-4"></th></tr></thead><tbody className="divide-y divide-slate-100">
          {items.map((item) => <tr key={item.id}><td className="px-6 py-4 font-semibold text-slate-800">{item.indicator.nama_indikator}<p className="mt-1 text-xs font-normal text-slate-400">{item.sub_indikator || "Tanpa subindikator"}</p></td><td className="px-6 py-4 text-slate-600">{item.deskripsi_periode}</td><td className="px-6 py-4 text-right font-bold text-[#102a43]">{new Intl.NumberFormat("id-ID", { maximumFractionDigits: 4 }).format(Number(item.nilai_data))}<p className="text-xs font-normal text-slate-400">{item.satuan}</p></td><td className="max-w-sm px-6 py-4 text-xs leading-5 text-slate-500"><p className="line-clamp-2">{item.analisis || "Analisis belum diisi."}</p><p className="mt-2 line-clamp-2 text-slate-400">{item.fenomena || "Fenomena belum diisi."}</p></td><td className="px-6 py-4"><div className="flex justify-end gap-2"><button onClick={() => edit(item)} title="Edit" className="rounded-lg bg-cyan-50 p-2 text-cyan-700"><PencilIcon className="h-4 w-4" /></button><button onClick={() => remove(item.id)} title="Hapus" className="rounded-lg bg-red-50 p-2 text-red-600"><TrashIcon className="h-4 w-4" /></button></div></td></tr>)}
          {!items.length && <tr><td colSpan={5} className="px-6 py-14 text-center text-slate-400">Belum ada data indikator.</td></tr>}
        </tbody></table></div></div>
      </div>
    </AppShell>
  );
}
