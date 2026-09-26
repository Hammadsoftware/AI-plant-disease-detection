import type { Metadata, Viewport } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "PlantAI — Plant Disease Diagnosis",
  description: "AI-powered plant disease diagnosis with evidence-backed research and treatment guidance.",
};

export const viewport: Viewport = {
  themeColor: "#083f2f",
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
