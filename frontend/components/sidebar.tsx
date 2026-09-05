"use client";

import { ChatBubbleLeftRightIcon, CheckBadgeIcon, ChartBarSquareIcon, CircleStackIcon, ClipboardDocumentListIcon, DocumentTextIcon, HomeIcon, RocketLaunchIcon, UserGroupIcon, UsersIcon } from "@heroicons/react/24/outline";
import Link from "next/link";
import { usePathname } from "next/navigation";

const groups = [
  { name: "Dashboard", icon: HomeIcon, href: "/dashboard", children: [] },
  {
    name: "Olah BRS", icon: DocumentTextIcon, href: "/brs",
    children: [
      { name: "Pendaftaran & Proses BRS", href: "/brs", icon: DocumentTextIcon },
      { name: "Pemeriksaan", href: "/checking", icon: ChartBarSquareIcon },
      { name: "Approval Kepala Kantor", href: "/approvals", icon: CheckBadgeIcon },
    ],
  },
  {
    name: "Rilis", icon: RocketLaunchIcon, href: "/releases",
    children: [
      { name: "Kegiatan Rilis", href: "/releases", icon: RocketLaunchIcon },
      { name: "Daftar Tamu", href: "/releases/guests", icon: UserGroupIcon },
      { name: "Q&A", href: "/releases/qna", icon: ChatBubbleLeftRightIcon },
      { name: "Laporan Rilis", href: "/releases/reports", icon: ClipboardDocumentListIcon },
    ],
  },
];

function activePath(pathname: string, href: string, exact = false) {
  return exact ? pathname === href : pathname === href || pathname.startsWith(`${href}/`);
}

export function Sidebar({ userLevel }: { userLevel: string }) {
  const pathname = usePathname();
  return <aside className="hidden min-h-screen w-72 shrink-0 bg-[#102a43] px-5 py-7 text-white lg:block">
    <div className="mb-10 px-3"><p className="text-xl font-bold tracking-wide">STATCHECK</p><p className="mt-1 text-xs text-slate-400">Quality before release</p></div>
    <nav className="space-y-3">
      {groups.map((group) => {
        const groupActive = group.name === "Olah BRS"
          ? ["/brs", "/checking", "/approvals"].some((path) => activePath(pathname, path))
          : activePath(pathname, group.href);
        const Icon = group.icon;
        return <div key={group.name} className={`rounded-xl ${groupActive ? "bg-white/5" : ""}`}>
          <Link href={group.href} className={`flex items-center gap-3 rounded-xl px-4 py-3 text-sm transition ${groupActive ? "bg-cyan-400 font-semibold text-[#102a43]" : "text-slate-200 hover:bg-white/10"}`}><Icon className="h-5 w-5" /><span>{group.name}</span></Link>
          {group.children.length > 0 && <div className="space-y-1 px-3 py-2">{group.children.map((child) => {
            const ChildIcon = child.icon;
            const exact = child.href === "/brs" || child.href === "/releases";
            const active = activePath(pathname, child.href, exact);
            return <Link key={child.name} href={child.href} className={`flex items-center gap-2 rounded-lg px-3 py-2 text-xs transition ${active ? "bg-white/10 font-semibold text-cyan-200" : "text-slate-400 hover:bg-white/5 hover:text-white"}`}><ChildIcon className="h-4 w-4" />{child.name}</Link>;
          })}</div>}
        </div>;
      })}
    </nav>
    {userLevel === "admin" && <div className="mt-8 border-t border-white/10 pt-6"><p className="px-3 text-[10px] font-bold uppercase tracking-[0.2em] text-slate-500">Administrasi</p><div className="mt-3 space-y-1"><Link href="/admin/users" className={`flex items-center gap-3 rounded-xl px-4 py-3 text-sm ${activePath(pathname, "/admin/users") ? "bg-white/10 text-cyan-200" : "text-slate-300 hover:bg-white/10"}`}><UsersIcon className="h-5 w-5" />Kelola User</Link><Link href="/indicators" className={`flex items-center gap-3 rounded-xl px-4 py-3 text-sm ${activePath(pathname, "/indicators") ? "bg-white/10 text-cyan-200" : "text-slate-300 hover:bg-white/10"}`}><CircleStackIcon className="h-5 w-5" />Kelola Indikator</Link></div></div>}
  </aside>;
}
