import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "STATCHECK",
  description: "Sistem pemeriksaan dan rilis Berita Resmi Statistik",
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="id">
      <body>{children}</body>
    </html>
  );
}
