import React from "react";
import Link from "next/link";
import { DisclaimerBanner } from "@/components/DisclaimerBanner";
import {
  Brain,
  ShieldCheck,
  Eye,
  Activity,
  ArrowRight,
  Sparkles,
  Layers,
  FileCheck2,
  Lock,
  Stethoscope
} from "lucide-react";

export default function LandingPage() {
  return (
    <div className="flex flex-col min-h-screen bg-[#070b14] clinical-grid">
      {/* 1. Persistent Top Safety Banner */}
      <DisclaimerBanner variant="top" />

      {/* 2. Navigation Header */}
      <header className="border-b border-slate-800 bg-[#090f20]/90 backdrop-blur-md px-6 py-4">
        <div className="max-w-7xl mx-auto flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-lg bg-gradient-to-br from-cyan-500/20 to-teal-500/10 border border-cyan-500/30 flex items-center justify-center text-cyan-400 shadow-inner">
              <Brain className="w-5 h-5" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <span className="font-semibold text-lg text-slate-100 tracking-tight">
                  NeuroScan <span className="text-cyan-400 font-mono text-sm uppercase">AI</span>
                </span>
                <span className="text-[10px] font-mono uppercase px-2 py-0.5 rounded-full bg-cyan-950/70 border border-cyan-800 text-cyan-300">
                  Research Prototype
                </span>
              </div>
              <p className="text-xs text-slate-400">
                Brain MRI Analysis & Calibrated Uncertainty Quantification
              </p>
            </div>
          </div>

          <Link
            href="/analyze"
            className="px-4 py-2 rounded-lg bg-cyan-600 hover:bg-cyan-500 text-slate-950 font-semibold text-xs font-mono transition flex items-center gap-2 shadow-lg shadow-cyan-600/20"
          >
            <span>Analyze a Scan</span>
            <ArrowRight className="w-3.5 h-3.5" />
          </Link>
        </div>
      </header>

      {/* 3. Hero Section */}
      <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 py-12 space-y-16">
        <section className="text-center space-y-6 max-w-3xl mx-auto pt-6">
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-cyan-950/70 border border-cyan-800 text-cyan-300 text-xs font-mono">
            <Sparkles className="w-3.5 h-3.5 text-cyan-400" />
            <span>Computer Vision Oncology Research</span>
          </div>

          <h1 className="text-3xl sm:text-5xl font-extrabold text-slate-100 tracking-tight leading-tight">
            Trustworthy Brain MRI Analysis with{" "}
            <span className="text-transparent bg-clip-text bg-gradient-to-r from-cyan-400 to-teal-300">
              Calibrated Uncertainty
            </span>
          </h1>

          <p className="text-base text-slate-300 leading-relaxed max-w-2xl mx-auto">
            NeuroScan AI evaluates brain MRI slices across four clinical categories. Unlike black-box neural networks, our pipeline validates scan authenticity, estimates statistical confidence variance, and highlights the anatomical evidence behind every prediction.
          </p>

          <div className="pt-2 flex flex-col sm:flex-row items-center justify-center gap-4">
            <Link
              href="/analyze"
              className="w-full sm:w-auto px-8 py-3.5 rounded-xl bg-cyan-500 hover:bg-cyan-400 text-slate-950 font-bold text-sm transition flex items-center justify-center gap-2 shadow-xl shadow-cyan-500/25 cursor-pointer"
            >
              <span>Analyze a Scan</span>
              <ArrowRight className="w-4 h-4" />
            </Link>
          </div>
        </section>

        {/* 4. Four Categories Classified */}
        <section className="space-y-6">
          <div className="text-center space-y-2">
            <h2 className="text-xl font-bold text-slate-100 tracking-tight">
              Classified Tumor & Tissue Categories
            </h2>
            <p className="text-xs text-slate-400 max-w-lg mx-auto">
              The model identifies specific intracranial lesion characteristics and structural patterns across four clinical classes.
            </p>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
            {/* Glioma */}
            <div className="bg-[#0b1224] border border-slate-800 rounded-xl p-5 space-y-2 hover:border-cyan-500/40 transition">
              <div className="w-8 h-8 rounded-lg bg-cyan-950 border border-cyan-800 flex items-center justify-center text-cyan-400 text-xs font-bold font-mono">
                01
              </div>
              <h3 className="text-base font-semibold text-slate-100">Glioma</h3>
              <p className="text-xs text-slate-400 leading-relaxed">
                Tumors arising from glial support cells in the central nervous system, varying from slow-growing lesions to aggressive infiltrating astrocytomas.
              </p>
            </div>

            {/* Meningioma */}
            <div className="bg-[#0b1224] border border-slate-800 rounded-xl p-5 space-y-2 hover:border-cyan-500/40 transition">
              <div className="w-8 h-8 rounded-lg bg-cyan-950 border border-cyan-800 flex items-center justify-center text-cyan-400 text-xs font-bold font-mono">
                02
              </div>
              <h3 className="text-base font-semibold text-slate-100">Meningioma</h3>
              <p className="text-xs text-slate-400 leading-relaxed">
                Typically slow-growing extra-axial tumors originating in the protective meningeal membranes that encase the brain and spinal cord.
              </p>
            </div>

            {/* Pituitary Tumor */}
            <div className="bg-[#0b1224] border border-slate-800 rounded-xl p-5 space-y-2 hover:border-cyan-500/40 transition">
              <div className="w-8 h-8 rounded-lg bg-cyan-950 border border-cyan-800 flex items-center justify-center text-cyan-400 text-xs font-bold font-mono">
                03
              </div>
              <h3 className="text-base font-semibold text-slate-100">Pituitary Tumor</h3>
              <p className="text-xs text-slate-400 leading-relaxed">
                Abnormal growths situated within the sella turcica at the skull base, commonly affecting hormonal balance and adjacent optic pathways.
              </p>
            </div>

            {/* No Tumor (Normal) */}
            <div className="bg-[#0b1224] border border-slate-800 rounded-xl p-5 space-y-2 hover:border-cyan-500/40 transition">
              <div className="w-8 h-8 rounded-lg bg-cyan-950 border border-cyan-800 flex items-center justify-center text-cyan-400 text-xs font-bold font-mono">
                04
              </div>
              <h3 className="text-base font-semibold text-slate-100">No Tumor (Normal)</h3>
              <p className="text-xs text-slate-400 leading-relaxed">
                MRI slices with preserved neuroanatomy, intact parenchymal symmetry, and no detectable mass effect or abnormal focal lesions.
              </p>
            </div>
          </div>
        </section>

        {/* 5. Core Safety & Interpretability Pillars */}
        <section className="space-y-6">
          <div className="text-center space-y-2">
            <h2 className="text-xl font-bold text-slate-100 tracking-tight">
              Safety & Explainability Pillars
            </h2>
            <p className="text-xs text-slate-400 max-w-lg mx-auto">
              How NeuroScan AI protects against out-of-distribution errors and explains its decisions.
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
            {/* Quality Gate */}
            <div className="bg-[#0b1224] border border-slate-800 rounded-xl p-6 flex items-start gap-4">
              <div className="p-3 rounded-lg bg-cyan-950 border border-cyan-800 text-cyan-400 shrink-0">
                <ShieldCheck className="w-6 h-6" />
              </div>
              <div className="space-y-1">
                <h3 className="text-sm font-semibold text-slate-100 font-mono">
                  Automated Quality & OOD Gate
                </h3>
                <p className="text-xs text-slate-400 leading-relaxed">
                  Checks that uploaded files exhibit genuine monochrome MRI characteristics and structured tissue histograms, immediately rejecting non-scan photos or corrupted uploads.
                </p>
              </div>
            </div>

            {/* Uncertainty Quantification */}
            <div className="bg-[#0b1224] border border-slate-800 rounded-xl p-6 flex items-start gap-4">
              <div className="p-3 rounded-lg bg-cyan-950 border border-cyan-800 text-cyan-400 shrink-0">
                <Activity className="w-6 h-6" />
              </div>
              <div className="space-y-1">
                <h3 className="text-sm font-semibold text-slate-100 font-mono">
                  Calibrated MC-Dropout Uncertainty
                </h3>
                <p className="text-xs text-slate-400 leading-relaxed">
                  Performs 20 stochastic sampling passes with temperature scaling to measure predictive stability, highlighting ambiguous scans that require human specialist review.
                </p>
              </div>
            </div>

            {/* Grad-CAM Explainability */}
            <div className="bg-[#0b1224] border border-slate-800 rounded-xl p-6 flex items-start gap-4">
              <div className="p-3 rounded-lg bg-cyan-950 border border-cyan-800 text-cyan-400 shrink-0">
                <Eye className="w-6 h-6" />
              </div>
              <div className="space-y-1">
                <h3 className="text-sm font-semibold text-slate-100 font-mono">
                  Grad-CAM Visual Heatmaps
                </h3>
                <p className="text-xs text-slate-400 leading-relaxed">
                  Generates gradient-weighted visual saliency overlays revealing the exact anatomical regions and tissue structures driving the network’s classification.
                </p>
              </div>
            </div>

            {/* Severity Heuristic */}
            <div className="bg-[#0b1224] border border-slate-800 rounded-xl p-6 flex items-start gap-4">
              <div className="p-3 rounded-lg bg-cyan-950 border border-cyan-800 text-cyan-400 shrink-0">
                <Layers className="w-6 h-6" />
              </div>
              <div className="space-y-1">
                <h3 className="text-sm font-semibold text-slate-100 font-mono">
                  Severity & Tissue Extent Heuristic
                </h3>
                <p className="text-xs text-slate-400 leading-relaxed">
                  Estimates relative foreground tissue volume using Otsu threshold segmentation, categorizing extent into Low, Medium, or High as an initial screening heuristic.
                </p>
              </div>
            </div>
          </div>
        </section>

        {/* 6. Call to Action Banner */}
        <section className="bg-gradient-to-r from-cyan-950/60 via-[#0b1224] to-teal-950/60 border border-cyan-800/40 rounded-2xl p-8 text-center space-y-4 shadow-2xl">
          <h2 className="text-2xl font-bold text-slate-100 tracking-tight">
            Ready to Evaluate a Scan?
          </h2>
          <p className="text-xs sm:text-sm text-slate-300 max-w-xl mx-auto">
            Upload an axial, coronal, or sagittal MRI slice, or test the interactive pipeline immediately using one of our verified clinical presets.
          </p>
          <div className="pt-2">
            <Link
              href="/analyze"
              className="inline-flex items-center gap-2 px-8 py-3 rounded-xl bg-cyan-500 hover:bg-cyan-400 text-slate-950 font-bold text-sm transition shadow-lg shadow-cyan-500/20 cursor-pointer"
            >
              <span>Launch Analysis Workstation</span>
              <ArrowRight className="w-4 h-4" />
            </Link>
          </div>
        </section>
      </main>

      {/* 7. Persistent Footer Disclaimer */}
      <DisclaimerBanner variant="footer" />
    </div>
  );
}
