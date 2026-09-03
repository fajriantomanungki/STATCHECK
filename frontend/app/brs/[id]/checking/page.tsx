"use client";

import {
  ArrowLeftIcon,
  ArrowPathIcon,
  CheckCircleIcon,
  ExclamationTriangleIcon,
  LightBulbIcon,
  PlayIcon,
  ShieldCheckIcon,
  XCircleIcon,
} from "@heroicons/react/24/outline";
import Link from "next/link";
import { useParams } from "next/navigation";
import { useEffect, useMemo, useState } from "react";

import { AppShell } from "@/components/app-shell";
import { getToken } from "@/lib/auth";
import {
  getBRS,
  getLatestCheck,
  reviewCheck,
  startCheck,
} from "@/services/api";
import type { BRS } from "@/types/phase2";
import type {
  CheckResult,
  CheckRunDetail,
  CheckSeverity,
  CheckType,
  ReviewAction,
} from "@/types/phase4";

const typeLabel: Record<CheckType, string> = {
  data_consistency: "Pemeriksaan Data Lama",
  document_coverage: "Kelengkapan 3 Dokumen",
  cross_document: "Konsistensi 3 Dokumen",
  language: "Bahasa",
};
const documentLabel: Record<string, string> = {
  bahan_publikasi: "BRS / Bahan Publikasi",
  bahan_paparan: "Bahan Paparan",
  narasi_pimpinan: "Narasi Pimpinan",
};
const statusLabel: Record<string, string> = {
  open: "Belum ditindaklanjuti",
  resolved: "Sudah diperbaiki",
  confirmed: "Data dikonfirmasi benar",
  ignored: "Warning diabaikan",
};
const severityStyle: Record<
  CheckSeverity,
  { label: string; className: string; icon: typeof XCircleIcon }
> = {
  error: {
    label: "Error",
    className: "bg-red-50 text-red-700",
    icon: XCircleIcon,
  },
  warning: {
    label: "Warning",
    className: "bg-amber-50 text-amber-700",
    icon: ExclamationTriangleIcon,
  },
  suggestion: {
    label: "Saran",
    className: "bg-blue-50 text-blue-700",
    icon: LightBulbIcon,
  },
};

function ScoreCard({
  label,
  value,
}: {
  label: string;
  value: string | number;
}) {
  const score = Number(value);
  const color =
    score >= 95
      ? "text-emerald-600"
      : score >= 80
        ? "text-amber-600"
        : "text-red-600";
  return (
    <div className="rounded-xl border border-slate-200 bg-white p-4">
      <p className="text-xs font-semibold uppercase tracking-wide text-slate-400">
        {label}
      </p>
      <p className={`mt-2 text-3xl font-bold ${color}`}>
        {score.toFixed(0)}
        <span className="text-sm font-medium text-slate-400">%</span>
      </p>
    </div>
  );
}

function FindingCard({
  finding,
  note,
  busy,
  onNote,
  onReview,
}: {
  finding: CheckResult;
  note: string;
  busy: boolean;
  onNote: (value: string) => void;
  onReview: (action: ReviewAction) => void;
}) {
  const severity = severityStyle[finding.severity];
  const Icon = severity.icon;
  const latestReview = finding.reviews.at(-1);
  const comparisonEntries = finding.comparison_values
    ? ["bahan_publikasi", "bahan_paparan", "narasi_pimpinan"].map(
        (documentType) => [
          documentType,
          finding.comparison_values?.[documentType],
        ] as const,
      )
    : [];
  const valueCounts = comparisonEntries.reduce<Record<string, number>>(
    (counts, [, item]) => {
      if (item?.value) counts[item.value] = (counts[item.value] || 0) + 1;
      return counts;
    },
    {},
  );
  const consensusValue = Object.entries(valueCounts).sort(
    (left, right) => right[1] - left[1],
  )[0];
  return (
    <article className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
      <div className="flex flex-col justify-between gap-3 sm:flex-row sm:items-start">
        <div className="flex items-start gap-3">
          <div className={`rounded-lg p-2 ${severity.className}`}>
            <Icon className="h-5 w-5" />
          </div>
          <div>
            <div className="flex flex-wrap items-center gap-2">
              <span
                className={`rounded-full px-2.5 py-1 text-xs font-bold ${severity.className}`}
              >
                {severity.label}
              </span>
              <span className="rounded-full bg-slate-100 px-2.5 py-1 text-xs font-semibold text-slate-600">
                {typeLabel[finding.check_type]}
              </span>
              {finding.document_type && (
                <span className="text-xs text-slate-400">
                  {documentLabel[finding.document_type] ||
                    finding.document_type}
                  {finding.page_number
                    ? ` • halaman/slide ${finding.page_number}`
                    : ""}
                </span>
              )}
            </div>
            <h3 className="mt-3 font-bold text-slate-800">
              {finding.field_name && finding.check_type !== "language"
                ? finding.field_name
                : finding.message}
            </h3>
            {finding.field_name && finding.check_type !== "language" && (
              <p className="mt-1 text-sm text-slate-600">{finding.message}</p>
            )}
          </div>
        </div>
        <span
          className={`shrink-0 rounded-full px-3 py-1 text-xs font-semibold ${finding.status === "open" ? "bg-slate-100 text-slate-600" : "bg-emerald-50 text-emerald-700"}`}
        >
          {statusLabel[finding.status] || finding.status}
        </span>
      </div>

      {comparisonEntries.length > 0 ? (
        <div className="mt-4 grid gap-3 lg:grid-cols-3">
          {comparisonEntries.map(([documentType, item]) => {
            const isConsensus = Boolean(
              item?.value &&
                consensusValue?.[1] >= 2 &&
                item.value === consensusValue[0],
            );
            const color = !item?.value
              ? "border-amber-200 bg-amber-50 text-amber-900"
              : isConsensus
                ? "border-emerald-200 bg-emerald-50 text-emerald-900"
                : finding.check_type === "cross_document"
                  ? "border-red-200 bg-red-50 text-red-900"
                  : "border-cyan-200 bg-cyan-50 text-cyan-900";
            return (
              <div key={documentType} className={`rounded-xl border p-4 ${color}`}>
                <p className="text-[11px] font-bold uppercase tracking-wide">
                  {item?.label || documentLabel[documentType] || documentType}
                </p>
                <p className="mt-2 text-xl font-bold">
                  {item?.value || "Tidak ditemukan"}
                </p>
                {item?.section_label && (
                  <p className="mt-1 text-xs opacity-70">
                    {item.section_label}
                  </p>
                )}
                {item?.context && (
                  <p className="mt-3 text-xs leading-5 opacity-80">
                    “{item.context}”
                  </p>
                )}
              </div>
            );
          })}
        </div>
      ) : (finding.expected_value || finding.actual_value) && (
        <div className="mt-4 grid gap-3 sm:grid-cols-2">
          <div className="rounded-xl bg-cyan-50 p-3">
            <p className="text-[11px] font-bold uppercase text-cyan-700">
              Nilai dokumen pertama
            </p>
            <p className="mt-1 font-bold text-cyan-900">
              {finding.expected_value || "—"}
            </p>
          </div>
          <div className="rounded-xl bg-red-50 p-3">
            <p className="text-[11px] font-bold uppercase text-red-600">
              Nilai dokumen pembanding
            </p>
            <p className="mt-1 font-bold text-red-800">
              {finding.actual_value || "Tidak memperoleh pasangan"}
            </p>
          </div>
        </div>
      )}
      {!finding.comparison_values && finding.context_text && (
        <div className="mt-4 rounded-xl border-l-4 border-slate-300 bg-slate-50 p-3 text-sm italic leading-6 text-slate-600">
          “{finding.context_text}”
        </div>
      )}
      {finding.suggestion && (
        <p className="mt-4 text-sm text-blue-700">
          <span className="font-bold">Saran:</span> {finding.suggestion}
        </p>
      )}

      {finding.status === "open" ? (
        <div className="mt-5 border-t border-slate-100 pt-4">
          <textarea
            value={note}
            onChange={(event) => onNote(event.target.value)}
            rows={2}
            placeholder="Catatan PJK (opsional)"
            className="w-full rounded-xl border border-slate-200 p-3 text-sm outline-none focus:border-cyan-500"
          />
          <div className="mt-3 flex flex-wrap gap-2">
            <button
              disabled={busy}
              onClick={() => onReview("fixed")}
              className="rounded-lg bg-emerald-600 px-3 py-2 text-xs font-semibold text-white disabled:opacity-50"
            >
              Sudah diperbaiki
            </button>
            <button
              disabled={busy}
              onClick={() => onReview("confirmed_correct")}
              className="rounded-lg bg-cyan-700 px-3 py-2 text-xs font-semibold text-white disabled:opacity-50"
            >
              Data memang benar
            </button>
            <button
              disabled={busy}
              onClick={() => onReview("ignored")}
              className="rounded-lg bg-slate-200 px-3 py-2 text-xs font-semibold text-slate-700 disabled:opacity-50"
            >
              Abaikan warning
            </button>
          </div>
        </div>
      ) : (
        latestReview && (
          <div className="mt-5 rounded-xl bg-emerald-50 p-3 text-sm text-emerald-800">
            <span className="font-bold">
              Tindak lanjut {latestReview.reviewer.nama}:
            </span>{" "}
            {latestReview.note || statusLabel[finding.status]}
          </div>
        )
      )}
    </article>
  );
}

export default function CheckingPage() {
  const { id } = useParams<{ id: string }>();
  const [brs, setBrs] = useState<BRS | null>(null);
  const [run, setRun] = useState<CheckRunDetail | null>(null);
  const [typeFilter, setTypeFilter] = useState<"all" | CheckType>("all");
  const [severityFilter, setSeverityFilter] = useState<"all" | CheckSeverity>(
    "all",
  );
  const [statusFilter, setStatusFilter] = useState("all");
  const [notes, setNotes] = useState<Record<string, string>>({});
  const [busy, setBusy] = useState(false);
  const [reviewing, setReviewing] = useState<string | null>(null);
  const [error, setError] = useState("");
  const [message, setMessage] = useState("");

  useEffect(() => {
    const token = getToken();
    if (!token) return;
    getBRS(token, id)
      .then(setBrs)
      .catch((err) => setError(err.message));
    getLatestCheck(token, id)
      .then(setRun)
      .catch((err) => {
        if (!err.message.includes("belum pernah")) setError(err.message);
      });
  }, [id]);

  const findings = useMemo(
    () =>
      (run?.results || []).filter(
        (item) =>
          (typeFilter === "all" || item.check_type === typeFilter) &&
          (severityFilter === "all" || item.severity === severityFilter) &&
          (statusFilter === "all" || item.status === statusFilter),
      ),
    [run, typeFilter, severityFilter, statusFilter],
  );
  const openCount =
    run?.results.filter((item) => item.status === "open").length || 0;
  const ready = Boolean(
    brs &&
    brs.jumlah_dokumen === 3 &&
    [
      "documents_uploaded",
      "pjk_review",
      "supervisor_revision",
      "ka_bps_revision",
    ].includes(brs.status),
  );

  async function runCheck() {
    const token = getToken();
    if (!token) return;
    setBusy(true);
    setError("");
    setMessage("");
    try {
      const result = await startCheck(token, id);
      setRun(result);
      setMessage(
        "Pemeriksaan otomatis selesai. Silakan tindak lanjuti setiap temuan.",
      );
      setBrs((current) =>
        current ? { ...current, status: "pjk_review" } : current,
      );
    } catch (err) {
      setError(
        err instanceof Error ? err.message : "Pemeriksaan gagal dijalankan.",
      );
    } finally {
      setBusy(false);
    }
  }

  async function submitReview(finding: CheckResult, action: ReviewAction) {
    const token = getToken();
    if (!token) return;
    setReviewing(finding.id);
    setError("");
    try {
      const updated = await reviewCheck(
        token,
        finding.id,
        action,
        notes[finding.id] || "",
      );
      setRun((current) =>
        current
          ? {
              ...current,
              results: current.results.map((item) =>
                item.id === updated.id ? updated : item,
              ),
            }
          : current,
      );
      setMessage("Tindak lanjut PJK berhasil disimpan.");
    } catch (err) {
      setError(
        err instanceof Error ? err.message : "Tindak lanjut gagal disimpan.",
      );
    } finally {
      setReviewing(null);
    }
  }

  return (
    <AppShell title="Hasil STATCHECK">
      <div className="p-6 lg:p-10">
        <Link
          href={`/brs/${id}`}
          className="inline-flex items-center gap-2 text-sm font-semibold text-slate-500 hover:text-cyan-700"
        >
          <ArrowLeftIcon className="h-4 w-4" />
          Kembali ke detail BRS
        </Link>
        <div className="mt-6 flex flex-col justify-between gap-5 lg:flex-row lg:items-end">
          <div>
            <p className="text-sm font-semibold uppercase tracking-widest text-cyan-700">
              Phase 8
            </p>
            <h1 className="mt-2 text-3xl font-bold text-slate-900">
              STATCHECK Result
            </h1>
            <p className="mt-2 text-slate-500">
              {brs?.nama_brs || "Memuat BRS..."}
            </p>
          </div>
          <button
            onClick={runCheck}
            disabled={!ready || busy}
            className="inline-flex items-center justify-center gap-2 rounded-xl bg-[#102a43] px-5 py-3 text-sm font-semibold text-white disabled:cursor-not-allowed disabled:opacity-40"
          >
            {run ? (
              <ArrowPathIcon
                className={`h-5 w-5 ${busy ? "animate-spin" : ""}`}
              />
            ) : (
              <PlayIcon className="h-5 w-5" />
            )}
            {busy
              ? "Sedang memeriksa..."
              : run
                ? "Jalankan Ulang"
                : "Mulai Pemeriksaan"}
          </button>
        </div>
        {!ready && brs && (
          <p className="mt-5 rounded-xl bg-amber-50 p-4 text-sm text-amber-800">
            Pemeriksaan memerlukan tiga dokumen aktif yang berhasil diekstrak:
            BRS/Bahan Publikasi, Bahan Paparan, dan Narasi Pimpinan. Saat ini
            tersedia {brs.jumlah_dokumen}/3 dokumen.
          </p>
        )}
        {error && (
          <p className="mt-5 rounded-xl bg-red-50 p-4 text-sm text-red-700">
            {error}
          </p>
        )}
        {message && (
          <p className="mt-5 rounded-xl bg-emerald-50 p-4 text-sm text-emerald-700">
            {message}
          </p>
        )}
        {run && openCount === 0 && brs?.status === "pjk_review" && (
          <div className="mt-5 flex flex-col justify-between gap-4 rounded-xl border border-emerald-200 bg-emerald-50 p-4 sm:flex-row sm:items-center">
            <div>
              <p className="font-semibold text-emerald-800">
                Semua temuan telah ditindaklanjuti.
              </p>
              <p className="mt-1 text-sm text-emerald-700">
                BRS siap masuk ke alur persetujuan Phase 5.
              </p>
            </div>
            <Link
              href={`/brs/${id}/approval`}
              className="shrink-0 rounded-xl bg-emerald-700 px-5 py-3 text-center text-sm font-semibold text-white"
            >
              Lanjut ke Persetujuan
            </Link>
          </div>
        )}

        {!run ? (
          <section className="mt-8 grid min-h-64 place-items-center rounded-2xl border border-dashed border-slate-300 bg-white p-8 text-center">
            <div>
              <ShieldCheckIcon className="mx-auto h-14 w-14 text-slate-300" />
              <h2 className="mt-4 text-lg font-bold text-slate-700">
                Belum ada hasil pemeriksaan
              </h2>
              <p className="mt-2 max-w-md text-sm leading-6 text-slate-500">
                Lengkapi tiga dokumen, lalu tekan Mulai Pemeriksaan untuk
                membandingkan BRS, bahan paparan, dan narasi pimpinan serta
                memeriksa bahasanya.
              </p>
            </div>
          </section>
        ) : (
          <>
            <section className="mt-7 grid gap-5 xl:grid-cols-[1.3fr_2fr]">
              <div className="rounded-2xl bg-[#102a43] p-6 text-white">
                <p className="text-xs font-semibold uppercase tracking-widest text-cyan-300">
                  Overall Score
                </p>
                <div className="mt-4 flex items-end gap-3">
                  <span className="text-6xl font-bold">
                    {Number(run.overall_score).toFixed(0)}
                  </span>
                  <span className="pb-2 text-xl text-slate-400">/100</span>
                </div>
                <div className="mt-6 grid grid-cols-2 gap-3 text-sm">
                  <div className="rounded-xl bg-white/10 p-3">
                    <p className="text-2xl font-bold text-emerald-300">
                      {run.passed_checks}
                    </p>
                    <p className="text-slate-300">Pemeriksaan lolos</p>
                  </div>
                  <div className="rounded-xl bg-white/10 p-3">
                    <p className="text-2xl font-bold text-amber-300">
                      {openCount}
                    </p>
                    <p className="text-slate-300">Perlu tindak lanjut</p>
                  </div>
                </div>
                <p className="mt-5 text-xs text-slate-400">
                  Diperiksa{" "}
                  {new Intl.DateTimeFormat("id-ID", {
                    dateStyle: "medium",
                    timeStyle: "short",
                  }).format(new Date(run.completed_at || run.started_at))}{" "}
                  • {run.engine_version}
                </p>
              </div>
              <div className="grid gap-4 sm:grid-cols-3">
                <ScoreCard
                  label="Kelengkapan 3 Dokumen"
                  value={run.data_consistency_score}
                />
                <ScoreCard
                  label="Konsistensi Angka"
                  value={run.cross_document_score}
                />
                <ScoreCard label="Bahasa" value={run.language_score} />
              </div>
            </section>

            <section className="mt-6 grid gap-4 sm:grid-cols-3">
              <div className="rounded-xl border border-red-100 bg-red-50 p-4">
                <p className="text-3xl font-bold text-red-700">
                  {run.error_count}
                </p>
                <p className="mt-1 text-sm font-semibold text-red-600">
                  Critical Error
                </p>
              </div>
              <div className="rounded-xl border border-amber-100 bg-amber-50 p-4">
                <p className="text-3xl font-bold text-amber-700">
                  {run.warning_count}
                </p>
                <p className="mt-1 text-sm font-semibold text-amber-600">
                  Warning
                </p>
              </div>
              <div className="rounded-xl border border-blue-100 bg-blue-50 p-4">
                <p className="text-3xl font-bold text-blue-700">
                  {run.suggestion_count}
                </p>
                <p className="mt-1 text-sm font-semibold text-blue-600">
                  Suggestion
                </p>
              </div>
            </section>

            <div className="mt-8 flex flex-col justify-between gap-4 lg:flex-row lg:items-center">
              <div>
                <h2 className="text-xl font-bold text-slate-800">
                  Daftar Temuan
                </h2>
                <p className="mt-1 text-sm text-slate-500">
                  Menampilkan {findings.length} dari {run.results.length}{" "}
                  temuan.
                </p>
              </div>
              <div className="flex flex-wrap gap-2">
                <select
                  value={typeFilter}
                  onChange={(e) =>
                    setTypeFilter(e.target.value as "all" | CheckType)
                  }
                  className="rounded-lg border border-slate-200 bg-white px-3 py-2 text-sm"
                >
                  <option value="all">Semua pemeriksaan</option>
                  <option value="document_coverage">
                    Kelengkapan 3 Dokumen
                  </option>
                  <option value="cross_document">Konsistensi 3 Dokumen</option>
                  <option value="language">Bahasa</option>
                </select>
                <select
                  value={severityFilter}
                  onChange={(e) =>
                    setSeverityFilter(e.target.value as "all" | CheckSeverity)
                  }
                  className="rounded-lg border border-slate-200 bg-white px-3 py-2 text-sm"
                >
                  <option value="all">Semua tingkat</option>
                  <option value="error">Error</option>
                  <option value="warning">Warning</option>
                  <option value="suggestion">Saran</option>
                </select>
                <select
                  value={statusFilter}
                  onChange={(e) => setStatusFilter(e.target.value)}
                  className="rounded-lg border border-slate-200 bg-white px-3 py-2 text-sm"
                >
                  <option value="all">Semua status</option>
                  <option value="open">Belum ditindaklanjuti</option>
                  <option value="resolved">Sudah diperbaiki</option>
                  <option value="confirmed">Dikonfirmasi benar</option>
                  <option value="ignored">Diabaikan</option>
                </select>
              </div>
            </div>
            <div className="mt-5 space-y-4">
              {findings.map((finding) => (
                <FindingCard
                  key={finding.id}
                  finding={finding}
                  note={notes[finding.id] || ""}
                  busy={reviewing === finding.id}
                  onNote={(value) =>
                    setNotes((current) => ({ ...current, [finding.id]: value }))
                  }
                  onReview={(action) => submitReview(finding, action)}
                />
              ))}
              {!findings.length && (
                <div className="rounded-2xl bg-emerald-50 p-8 text-center text-emerald-700">
                  <CheckCircleIcon className="mx-auto h-10 w-10" />
                  <p className="mt-3 font-semibold">
                    Tidak ada temuan pada filter ini.
                  </p>
                </div>
              )}
            </div>
          </>
        )}
      </div>
    </AppShell>
  );
}
