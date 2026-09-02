"use client";

import {
  ArrowDownTrayIcon,
  ArrowLeftIcon,
  ArrowPathIcon,
  CheckCircleIcon,
  ClockIcon,
  DocumentArrowUpIcon,
  DocumentMagnifyingGlassIcon,
  ExclamationTriangleIcon,
} from "@heroicons/react/24/outline";
import Link from "next/link";
import { useParams } from "next/navigation";
import { ChangeEvent, useCallback, useEffect, useMemo, useState } from "react";

import { AppShell } from "@/components/app-shell";
import { getToken } from "@/lib/auth";
import {
  downloadDocument,
  getBRS,
  getDocument,
  getDocuments,
  reextractDocument,
  uploadDocument,
} from "@/services/api";
import type { BRS } from "@/types/phase2";
import type { BRSDocument, BRSDocumentDetail, DocumentType } from "@/types/phase3";

const documentTypes: { type: DocumentType; title: string; description: string }[] = [
  { type: "bahan_publikasi", title: "Bahan Publikasi", description: "Naskah publikasi resmi BRS" },
  { type: "bahan_paparan", title: "Bahan Paparan", description: "Slide atau materi presentasi" },
  { type: "narasi_pimpinan", title: "Narasi Pimpinan", description: "Naskah yang dibacakan pimpinan" },
];

function formatSize(bytes: number) {
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / 1024 / 1024).toFixed(1)} MB`;
}

function ExtractionBadge({ document }: { document: BRSDocument }) {
  if (document.extraction_status === "completed") {
    return <span className="inline-flex items-center gap-1 rounded-full bg-emerald-50 px-2.5 py-1 text-xs font-semibold text-emerald-700"><CheckCircleIcon className="h-4 w-4" />Teks diekstrak</span>;
  }
  if (document.extraction_status === "failed") {
    return <span className="inline-flex items-center gap-1 rounded-full bg-red-50 px-2.5 py-1 text-xs font-semibold text-red-700"><ExclamationTriangleIcon className="h-4 w-4" />Ekstraksi gagal</span>;
  }
  return <span className="inline-flex items-center gap-1 rounded-full bg-amber-50 px-2.5 py-1 text-xs font-semibold text-amber-700"><ClockIcon className="h-4 w-4" />Menunggu ekstraksi</span>;
}

export default function BRSDocumentsPage() {
  const { id } = useParams<{ id: string }>();
  const [brs, setBrs] = useState<BRS | null>(null);
  const [documents, setDocuments] = useState<BRSDocument[]>([]);
  const [selectedFiles, setSelectedFiles] = useState<Partial<Record<DocumentType, File>>>({});
  const [busyType, setBusyType] = useState<DocumentType | null>(null);
  const [selected, setSelected] = useState<BRSDocumentDetail | null>(null);
  const [loadingDetail, setLoadingDetail] = useState(false);
  const [error, setError] = useState("");
  const [message, setMessage] = useState("");

  const load = useCallback(async () => {
    const token = getToken();
    if (!token) return;
    const [brsResult, documentResult] = await Promise.all([getBRS(token, id), getDocuments(token, id, true)]);
    setBrs(brsResult);
    setDocuments(documentResult);
  }, [id]);

  useEffect(() => {
    const token = getToken();
    if (!token) return;
    Promise.all([getBRS(token, id), getDocuments(token, id, true)])
      .then(([brsResult, documentResult]) => {
        setBrs(brsResult);
        setDocuments(documentResult);
      })
      .catch((err) => setError(err.message));
  }, [id]);

  const activeByType = useMemo(() => {
    const result = new Map<DocumentType, BRSDocument>();
    documents.filter((item) => item.status === "active").forEach((item) => result.set(item.document_type, item));
    return result;
  }, [documents]);

  function chooseFile(type: DocumentType, event: ChangeEvent<HTMLInputElement>) {
    const file = event.target.files?.[0];
    if (file) setSelectedFiles((current) => ({ ...current, [type]: file }));
  }

  async function submitUpload(type: DocumentType) {
    const token = getToken();
    const file = selectedFiles[type];
    if (!token || !file) return;
    setBusyType(type);
    setError("");
    setMessage("");
    try {
      const result = await uploadDocument(token, id, type, file);
      setSelectedFiles((current) => ({ ...current, [type]: undefined }));
      setSelected(result);
      setMessage(`${file.name} berhasil diunggah sebagai versi ${result.version}.`);
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Dokumen gagal diunggah.");
    } finally {
      setBusyType(null);
    }
  }

  async function showDetail(document: BRSDocument) {
    const token = getToken();
    if (!token) return;
    setLoadingDetail(true);
    setError("");
    try { setSelected(await getDocument(token, document.id)); }
    catch (err) { setError(err instanceof Error ? err.message : "Detail dokumen gagal dimuat."); }
    finally { setLoadingDetail(false); }
  }

  async function handleDownload(document: BRSDocument) {
    const token = getToken();
    if (!token) return;
    try { await downloadDocument(token, document); }
    catch (err) { setError(err instanceof Error ? err.message : "Dokumen gagal diunduh."); }
  }

  async function handleReextract(document: BRSDocument) {
    const token = getToken();
    if (!token) return;
    setBusyType(document.document_type);
    setError("");
    try {
      const result = await reextractDocument(token, document.id);
      setSelected(result);
      setMessage(result.extraction_status === "completed" ? "Ekstraksi teks berhasil dijalankan ulang." : "Ekstraksi masih gagal. Periksa file sumber.");
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Ekstraksi ulang gagal.");
    } finally { setBusyType(null); }
  }

  return (
    <AppShell title="Dokumen BRS">
      <div className="p-6 lg:p-10">
        <Link href={`/brs/${id}`} className="inline-flex items-center gap-2 text-sm font-semibold text-slate-500 hover:text-cyan-700"><ArrowLeftIcon className="h-4 w-4" />Kembali ke detail BRS</Link>
        <div className="mt-6 flex flex-col justify-between gap-4 md:flex-row md:items-end">
          <div><p className="text-sm font-semibold uppercase tracking-widest text-cyan-700">Phase 3</p><h1 className="mt-2 text-3xl font-bold text-slate-900">Dokumen BRS</h1><p className="mt-2 text-slate-500">{brs?.nama_brs || "Memuat BRS..."}</p></div>
          <div className="rounded-xl bg-[#102a43] px-5 py-3 text-sm text-white"><span className="text-slate-300">Kelengkapan</span><strong className="ml-3 text-lg">{activeByType.size}/3</strong></div>
        </div>

        {error && <p className="mt-5 rounded-xl bg-red-50 p-4 text-sm text-red-700">{error}</p>}
        {message && <p className="mt-5 rounded-xl bg-emerald-50 p-4 text-sm text-emerald-700">{message}</p>}

        <div className="mt-7 grid gap-5 xl:grid-cols-3">
          {documentTypes.map((config) => {
            const current = activeByType.get(config.type);
            const history = documents.filter((item) => item.document_type === config.type && item.status === "archived");
            const file = selectedFiles[config.type];
            return <section key={config.type} className="flex flex-col rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
              <div className="flex items-start justify-between gap-3"><div><h2 className="font-bold text-slate-800">{config.title}</h2><p className="mt-1 text-xs text-slate-400">{config.description}</p></div><DocumentArrowUpIcon className="h-7 w-7 shrink-0 text-cyan-700" /></div>

              <div className="mt-5 min-h-32 rounded-xl bg-slate-50 p-4">
                {current ? <><div className="flex items-center justify-between gap-2"><span className="rounded-md bg-white px-2 py-1 text-xs font-bold text-slate-600">VERSI {current.version}</span><ExtractionBadge document={current} /></div><p className="mt-3 truncate font-semibold text-slate-700" title={current.file_name}>{current.file_name}</p><p className="mt-1 text-xs text-slate-400">{formatSize(current.file_size)} • {current.page_count} halaman/slide • {current.extracted_char_count.toLocaleString("id-ID")} karakter</p><div className="mt-4 flex flex-wrap gap-2"><button onClick={() => showDetail(current)} className="inline-flex items-center gap-1 rounded-lg bg-cyan-50 px-3 py-2 text-xs font-semibold text-cyan-800"><DocumentMagnifyingGlassIcon className="h-4 w-4" />Lihat teks</button><button onClick={() => handleDownload(current)} className="inline-flex items-center gap-1 rounded-lg bg-slate-200 px-3 py-2 text-xs font-semibold text-slate-700"><ArrowDownTrayIcon className="h-4 w-4" />Unduh</button>{current.extraction_status === "failed" && <button onClick={() => handleReextract(current)} className="inline-flex items-center gap-1 rounded-lg bg-amber-50 px-3 py-2 text-xs font-semibold text-amber-700"><ArrowPathIcon className="h-4 w-4" />Ulangi</button>}</div></> : <div className="flex h-24 items-center justify-center text-center text-sm text-slate-400">Dokumen belum diunggah.</div>}
              </div>

              <label className="mt-4 block cursor-pointer rounded-xl border border-dashed border-slate-300 p-3 text-center text-sm text-slate-500 hover:border-cyan-500 hover:bg-cyan-50/40"><input type="file" accept=".pdf,.pptx,.docx" className="hidden" onChange={(event) => chooseFile(config.type, event)} />{file ? <span className="font-semibold text-cyan-800">{file.name}</span> : "Pilih PDF, PPTX, atau DOCX"}</label>
              <button disabled={!file || busyType !== null} onClick={() => submitUpload(config.type)} className="mt-3 rounded-xl bg-[#102a43] px-4 py-3 text-sm font-semibold text-white disabled:cursor-not-allowed disabled:opacity-40">{busyType === config.type ? "Memproses dokumen..." : current ? "Unggah Versi Baru" : "Unggah Dokumen"}</button>

              {history.length > 0 && <details className="mt-4 border-t border-slate-100 pt-3"><summary className="cursor-pointer text-xs font-semibold text-slate-500">Riwayat versi ({history.length})</summary><div className="mt-3 space-y-2">{history.map((item) => <div key={item.id} className="flex items-center justify-between gap-2 rounded-lg bg-slate-50 p-2 text-xs"><button onClick={() => showDetail(item)} className="min-w-0 truncate text-left font-semibold text-slate-600 hover:text-cyan-700">v{item.version} — {item.file_name}</button><button onClick={() => handleDownload(item)} title="Unduh versi ini"><ArrowDownTrayIcon className="h-4 w-4 text-slate-400" /></button></div>)}</div></details>}
            </section>;
          })}
        </div>

        {(selected || loadingDetail) && <section className="mt-7 rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
          {loadingDetail ? <p className="text-sm text-slate-400">Memuat hasil ekstraksi...</p> : selected && <><div className="flex flex-col justify-between gap-3 md:flex-row md:items-start"><div><p className="text-xs font-bold uppercase tracking-wider text-cyan-700">Hasil Ekstraksi • Versi {selected.version}</p><h2 className="mt-1 text-xl font-bold text-slate-800">{selected.file_name}</h2><p className="mt-1 text-sm text-slate-400">Teks ini akan menjadi bahan pemeriksaan otomatis pada Phase 4.</p></div><button onClick={() => setSelected(null)} className="self-start rounded-lg bg-slate-100 px-3 py-2 text-xs font-semibold text-slate-600">Tutup</button></div>{selected.extraction_error && <p className="mt-5 rounded-xl bg-red-50 p-4 text-sm text-red-700">{selected.extraction_error}</p>}<div className="mt-5 space-y-4">{selected.contents.map((content) => <article key={content.id} className="rounded-xl border border-slate-200"><h3 className="border-b border-slate-100 bg-slate-50 px-4 py-3 text-sm font-bold text-slate-600">{content.section_label}</h3><pre className="max-h-96 overflow-auto whitespace-pre-wrap p-4 font-sans text-sm leading-6 text-slate-700">{content.text_content || "Tidak ada teks yang dapat diekstrak pada bagian ini."}</pre></article>)}{!selected.contents.length && !selected.extraction_error && <p className="text-sm text-slate-400">Tidak ada teks yang ditemukan.</p>}</div></>}
        </section>}
      </div>
    </AppShell>
  );
}
