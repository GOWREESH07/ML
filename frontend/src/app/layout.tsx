import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "NeuroScan AI — Brain Tumor MRI Analysis & Uncertainty Quantification",
  description: "Educational and research platform for brain tumor MRI classification, Monte Carlo Dropout uncertainty estimation, and Grad-CAM interpretability.",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className="dark antialiased">
      <body className="min-h-screen bg-[#070b14] text-slate-100 flex flex-col selection:bg-cyan-500/20 selection:text-cyan-300 font-sans">
        {children}
      </body>
    </html>
  );
}
