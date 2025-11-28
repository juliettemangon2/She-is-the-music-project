// frontend/app/layout.tsx
import type { Metadata } from "next";
import "./globals.css";
import { Sidebar } from "../components/Sidebar";
import { SongProvider } from "../context/SongContext";

export const metadata: Metadata = {
  title: "Music Data Tool",
  description: "Metadata and collaboration insights for songs",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body className="app-body">
        <SongProvider>
          <Sidebar />
          <main className="main">{children}</main>
        </SongProvider>
      </body>
    </html>
  );
}