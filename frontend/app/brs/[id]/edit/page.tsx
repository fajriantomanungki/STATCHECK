"use client";

import { useParams } from "next/navigation";
import { useEffect, useState } from "react";

import { AppShell } from "@/components/app-shell";
import { BRSForm } from "@/components/brs-form";
import { getToken } from "@/lib/auth";
import { getBRS } from "@/services/api";
import type { BRSForm as BRSFormType } from "@/types/phase2";

export default function EditBRSPage() {
  const { id } = useParams<{ id: string }>();
  const [initial, setInitial] = useState<BRSFormType | null>(null);
  useEffect(() => { const token = getToken(); if (token) getBRS(token, id).then((brs) => setInitial({ nama_brs: brs.nama_brs, waktu_rilis: brs.waktu_rilis, fungsi_pj: brs.fungsi_pj, supervisor_id: brs.supervisor?.id || null, team_user_ids: brs.team?.map((member) => member.user.id) || [] })); }, [id]);
  return <AppShell title="Edit BRS"><div className="mx-auto max-w-5xl p-6 lg:p-10"><div className="mb-7"><p className="text-sm font-semibold uppercase tracking-widest text-cyan-700">Phase 2</p><h1 className="mt-2 text-3xl font-bold text-slate-900">Edit Registrasi BRS</h1></div>{initial ? <BRSForm initialValue={initial} brsId={id} /> : <p className="text-sm text-slate-400">Memuat BRS...</p>}</div></AppShell>;
}
