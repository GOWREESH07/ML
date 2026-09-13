"use client";

import React, { useState } from "react";
import {
  AlertTriangle,
  CheckCircle2,
  ChevronDown,
  ChevronUp,
  Sliders,
  HelpCircle,
  Eye,
  Activity,
  Layers,
  FileText,
  ShieldCheck,
  Stethoscope
} from "lucide-react";
import { PredictionResult } from "@/types";

interface ResultsSectionProps {
  result: PredictionResult;
  originalImageUrl: string | null;
}

export const ResultsSection: React.FC<ResultsSectionProps> = ({
  result,
  originalImageUrl,
}) => {
  const [accordionOpen, setAccordionOpen] = useState(true);
  const [blendOpacity, setBlendOpacity] = useState<number>(0.5);
  const [activeViewMode, setActiveViewMode] = useState<"side-by-side" | "interactive-blend">("side-by-side");

  // Uncertainty evaluation: green / amber / red
  const getUncertaintyColor = (unc: number) => {
    if (unc < 0.05) {
      return {
        badge: "bg-emerald-950/80 border-emerald-500/50 text-emerald-300",
        dot: "bg-emerald-400",
        label: "Low Uncertainty (Reliable Sampling)",
      };
    }
    if (unc <= 0.08) {
      return {
        badge: "bg-amber-950/80 border-amber-500/50 text-amber-300",
        dot: "bg-amber-400",
        label: "Moderate Uncertainty",
      };
    }
    return {
      badge: "bg-rose-950/80 border-rose-500/60 text-rose-300 animate-pulse",
      dot: "bg-rose-400",
      label: "High Uncertainty (Review Recommended)",
    };
  };

  const uncStyle = getUncertaintyColor(result.uncertainty);

  // Severity badge style
  const getSeverityStyle = (bucket: string) => {
    switch (bucket.toLowerCase()) {
      case "low":
        return "bg-slate-800 border-slate-700 text-cyan-300";
      case "medium":
        return "bg-cyan-950/80 border-cyan-700/60 text-cyan-200";
      case "high":
        return "bg-indigo-950/80 border-indigo-700/60 text-indigo-200";
      default:
        return "bg-slate-800 border-slate-700 text-slate-300";
    }
  };

  const classDisplayNames: Record<string, string> = {
    glioma: "Glioma",
    meningioma: "Meningioma",
    notumor: "No Tumor (Normal)",
    pituitary: "Pituitary Tumor",
  };

  return (
    <div className="w-full space-y-6 animate-in fade-in duration-500">
      {/* 1. Low Confidence Alert Banner */}
      {result.low_confidence_flag && (
        <div className="w-full bg-rose-950/80 border-2 border-rose-500/80 rounded-xl p-4 md:p-5 shadow-xl shadow-rose-950/30 flex flex-col sm:flex-row items-start gap-4">
          <div className="p-2.5 rounded-lg bg-rose-900/60 border border-rose-500/40 text-rose-300 shrink-0">
            <AlertTriangle className="w-6 h-6 animate-bounce" />
          </div>
          <div className="flex-1">
            <h3 className="text-sm md:text-base font-bold text-rose-200 tracking-wide uppercase flex items-center gap-2">
              Elevated Uncertainty Detected — Specialist Review Required
            </h3>
            <p className="text-xs md:text-sm text-rose-200/90 mt-1 leading-relaxed">
              Stochastic Monte Carlo sampling indicates elevated predictive variance (uncertainty: {(result.uncertainty * 100).toFixed(1)}% or lower confidence margin). The scan features may be subtle, border-zone, or contain image acquisition artifacts.
            </p>
            <div className="mt-2.5 inline-flex items-center gap-2 text-xs font-semibold px-3 py-1 rounded bg-rose-900/40 border border-rose-500/30 text-rose-300">
              <Stethoscope className="w-3.5 h-3.5" />
              Recommendation: Do not rely on automated inference. Request formal re-scan or board-certified neuro-radiology review.
            </div>
          </div>
        </div>
      )}

      {/* 2. Top Metric Cards Grid */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        {/* Card 1: Prediction */}
        <div className="bg-[#0b1224] border border-slate-800 rounded-xl p-5 shadow-lg relative overflow-hidden">
          <div className="flex items-center justify-between text-slate-400 text-xs mb-2">
            <span className="font-mono uppercase tracking-wider">Classification</span>
            <Layers className="w-4 h-4 text-cyan-400" />
          </div>
          <div className="text-xl font-bold text-slate-100 tracking-tight capitalize">
            {classDisplayNames[result.predicted_class] || result.predicted_class}
          </div>
          <div className="mt-2 flex items-center gap-1.5 text-xs text-slate-400 font-mono">
            <span>Class Index:</span>
            <span className="text-cyan-300 font-semibold">{result.predicted_class}</span>
          </div>
        </div>

        {/* Card 2: Confidence */}
        <div className="bg-[#0b1224] border border-slate-800 rounded-xl p-5 shadow-lg">
          <div className="flex items-center justify-between text-slate-400 text-xs mb-2">
            <span className="font-mono uppercase tracking-wider">Mean Confidence</span>
            <Activity className="w-4 h-4 text-cyan-400" />
          </div>
          <div className="flex items-baseline gap-2">
            <span className="text-2xl font-bold text-slate-100 font-mono">
              {(result.confidence * 100).toFixed(1)}%
            </span>
            <span className="text-xs text-slate-400 font-mono">20-pass avg</span>
          </div>
          <div className="w-full bg-slate-800 h-2 rounded-full mt-3 overflow-hidden">
            <div
              className="bg-gradient-to-r from-cyan-600 to-teal-400 h-full rounded-full transition-all duration-700"
              style={{ width: `${Math.min(100, Math.max(0, result.confidence * 100))}%` }}
            />
          </div>
        </div>

        {/* Card 3: MC-Dropout Uncertainty */}
        <div className="bg-[#0b1224] border border-slate-800 rounded-xl p-5 shadow-lg">
          <div className="flex items-center justify-between text-slate-400 text-xs mb-2">
            <span className="font-mono uppercase tracking-wider">MC Uncertainty (std)</span>
            <span className={`w-2.5 h-2.5 rounded-full ${uncStyle.dot}`} />
          </div>
          <div className="flex items-baseline gap-2">
            <span className="text-2xl font-bold font-mono text-slate-100">
              ±{(result.uncertainty * 100).toFixed(1)}%
            </span>
          </div>
          <div className="mt-2.5">
            <span
              className={`inline-flex items-center gap-1.5 text-[11px] font-mono px-2.5 py-0.5 rounded-full border ${uncStyle.badge}`}
            >
              {uncStyle.label}
            </span>
          </div>
        </div>

        {/* Card 4: Severity / Extent Heuristic */}
        <div className="bg-[#0b1224] border border-slate-800 rounded-xl p-5 shadow-lg group relative">
          <div className="flex items-center justify-between text-slate-400 text-xs mb-2">
            <span className="font-mono uppercase tracking-wider flex items-center gap-1">
              Severity / Extent
              <span
                className="cursor-help text-slate-400 hover:text-slate-300"
                title="heuristic estimate, not a clinical grading"
              >
                <HelpCircle className="w-3.5 h-3.5" />
              </span>
            </span>
            <FileText className="w-4 h-4 text-cyan-400" />
          </div>
          <div className="flex items-baseline gap-2">
            <span
              className={`text-sm font-semibold uppercase px-3 py-1 rounded-md border font-mono ${getSeverityStyle(
                result.severity_bucket
              )}`}
            >
              {result.severity_bucket} Extent
            </span>
          </div>
          <div className="mt-2.5 text-[11px] text-slate-400 font-mono">
            Otsu foreground: {(result.foreground_ratio * 100).toFixed(1)}%
          </div>

          {/* Mandatory Tooltip Disclaimer */}
          <div className="mt-1 text-[10px] text-slate-400 italic">
            *heuristic estimate, not a clinical grading
          </div>
        </div>
      </div>

      {/* 3. Visual Interpretability Section (Original vs Grad-CAM) */}
      <div className="bg-[#0b1224] border border-slate-800 rounded-xl p-6 shadow-xl">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-slate-800">
          <div>
            <h3 className="text-base font-semibold text-slate-100 flex items-center gap-2">
              <Eye className="w-5 h-5 text-cyan-400" />
              Grad-CAM Visual Explanations & Saliency Map
            </h3>
            <p className="text-xs text-slate-400 mt-0.5">
              Features weighted from the 5th convolutional block showing regions that most strongly drove the {classDisplayNames[result.predicted_class] || result.predicted_class} classification.
            </p>
          </div>

          {/* View mode buttons & slider */}
          <div className="flex flex-wrap items-center gap-3">
            <div className="flex rounded-lg bg-slate-900 border border-slate-800 p-0.5">
              <button
                type="button"
                onClick={() => setActiveViewMode("side-by-side")}
                className={`px-3 py-1 text-xs rounded-md font-mono transition cursor-pointer ${
                  activeViewMode === "side-by-side"
                    ? "bg-cyan-950 text-cyan-300 border border-cyan-700/50"
                    : "text-slate-400 hover:text-slate-200"
                }`}
              >
                Side-by-Side
              </button>
              <button
                type="button"
                onClick={() => setActiveViewMode("interactive-blend")}
                className={`px-3 py-1 text-xs rounded-md font-mono transition cursor-pointer ${
                  activeViewMode === "interactive-blend"
                    ? "bg-cyan-950 text-cyan-300 border border-cyan-700/50"
                    : "text-slate-400 hover:text-slate-200"
                }`}
              >
                Overlay Blending
              </button>
            </div>
          </div>
        </div>

        {/* Viewport Render */}
        {activeViewMode === "side-by-side" ? (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mt-6">
            {/* Original MRI Slice */}
            <div className="flex flex-col items-center">
              <div className="w-full text-xs font-mono text-slate-400 mb-2 flex items-center justify-between">
                <span>Input Brain MRI Slice</span>
                <span className="text-slate-400">Native Resolution</span>
              </div>
              <div className="w-full aspect-square max-w-[420px] bg-black rounded-xl border border-slate-800 p-2 flex items-center justify-center overflow-hidden shadow-inner">
                {originalImageUrl ? (
                  // eslint-disable-next-line @next/next/no-img-element
                  <img
                    src={originalImageUrl}
                    alt="Original MRI Slice"
                    className="max-h-full max-w-full object-contain rounded-lg"
                  />
                ) : (
                  <div className="text-xs text-slate-400 font-mono">Original image preview unavailable</div>
                )}
              </div>
              <span className="text-[11px] text-slate-400 mt-2 font-mono">
                Anatomical Baseline Grayscale Scan
              </span>
            </div>

            {/* Grad-CAM Heatmap Overlay */}
            <div className="flex flex-col items-center">
              <div className="w-full text-xs font-mono text-slate-400 mb-2 flex items-center justify-between">
                <span className="text-cyan-400">Grad-CAM Saliency Overlay</span>
                <span className="text-cyan-400 font-bold">Jet Colormap (50% blend)</span>
              </div>
              <div className="w-full aspect-square max-w-[420px] bg-black rounded-xl border border-cyan-950 p-2 flex items-center justify-center overflow-hidden shadow-inner relative group">
                {/* eslint-disable-next-line @next/next/no-img-element */}
                <img
                  src={result.heatmap_base64}
                  alt="Grad-CAM Heatmap Overlay"
                  className="max-h-full max-w-full object-contain rounded-lg"
                />
              </div>
              <span className="text-[11px] text-cyan-400 mt-2 font-mono">
                Red/Yellow: High Attention • Blue/Cyan: Background Baseline
              </span>
            </div>
          </div>
        ) : (
          /* Interactive Blend Mode */
          <div className="flex flex-col items-center mt-6">
            <div className="w-full max-w-[500px] mb-4 flex items-center gap-4 bg-slate-900/80 border border-slate-800 rounded-lg p-3">
              <Sliders className="w-4 h-4 text-cyan-400 shrink-0" />
              <div className="flex-1">
                <div className="flex justify-between text-xs font-mono text-slate-400 mb-1">
                  <span>Original Scan</span>
                  <span>Heatmap Opacity: {Math.round(blendOpacity * 100)}%</span>
                  <span>Full Heatmap</span>
                </div>
                <input
                  type="range"
                  min="0"
                  max="1"
                  step="0.05"
                  value={blendOpacity}
                  onChange={(e) => setBlendOpacity(parseFloat(e.target.value))}
                  className="w-full accent-cyan-400 cursor-pointer"
                />
              </div>
            </div>

            <div className="relative w-full aspect-square max-w-[460px] bg-black rounded-xl border border-slate-800 p-2 flex items-center justify-center overflow-hidden shadow-2xl">
              {originalImageUrl && (
                // eslint-disable-next-line @next/next/no-img-element
                <img
                  src={originalImageUrl}
                  alt="Base MRI"
                  className="absolute inset-0 w-full h-full object-contain p-2"
                />
              )}
              {/* eslint-disable-next-line @next/next/no-img-element */}
              <img
                src={result.heatmap_base64}
                alt="Heatmap Layer"
                style={{ opacity: blendOpacity }}
                className="absolute inset-0 w-full h-full object-contain p-2 transition-opacity duration-150"
              />
            </div>
            <p className="text-xs text-slate-400 mt-3 font-mono">
              Adjust the slider above to transition between the anatomical MRI scan and the convolutional saliency map.
            </p>
          </div>
        )}
      </div>

      {/* 4. Multi-Class Probability Distribution */}
      {result.class_probabilities && (
        <div className="bg-[#0b1224] border border-slate-800 rounded-xl p-6 shadow-xl">
          <h3 className="text-sm font-semibold text-slate-100 flex items-center gap-2 mb-1">
            <Activity className="w-4 h-4 text-cyan-400" />
            Class Probability & Uncertainty Distribution
          </h3>
          <p className="text-xs text-slate-400 mb-4">
            Monte Carlo sampling across 20 stochastic passes with dropout active. Error margins denote ±1 standard deviation.
          </p>

          <div className="space-y-3.5">
            {Object.entries(result.class_probabilities).map(([cls, prob]) => {
              const unc = result.class_uncertainties ? result.class_uncertainties[cls] || 0 : 0;
              const isPred = cls === result.predicted_class;

              return (
                <div key={cls} className="space-y-1">
                  <div className="flex items-center justify-between text-xs font-mono">
                    <div className="flex items-center gap-2">
                      <span className={`capitalize ${isPred ? "text-cyan-300 font-bold" : "text-slate-300"}`}>
                        {classDisplayNames[cls] || cls}
                      </span>
                      {isPred && (
                        <span className="text-[10px] uppercase px-1.5 py-0.2 rounded bg-cyan-950 border border-cyan-700 text-cyan-300">
                          Selected
                        </span>
                      )}
                    </div>
                    <div className="text-slate-400 flex items-center gap-2">
                      <span className={isPred ? "text-slate-100 font-bold" : "text-slate-400"}>
                        {(prob * 100).toFixed(1)}%
                      </span>
                      <span className="text-slate-400 text-[11px]">
                        (±{(unc * 100).toFixed(1)}%)
                      </span>
                    </div>
                  </div>

                  <div className="w-full bg-slate-900 h-2.5 rounded-full overflow-hidden border border-slate-800">
                    <div
                      className={`h-full rounded-full transition-all duration-500 ${
                        isPred
                          ? "bg-gradient-to-r from-cyan-500 to-teal-400"
                          : "bg-slate-700"
                      }`}
                      style={{ width: `${Math.max(1, Math.min(100, prob * 100))}%` }}
                    />
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* 5. Clinical Knowledge Base Accordion */}
      <div className="bg-[#0b1224] border border-slate-800 rounded-xl shadow-xl overflow-hidden">
        <button
          type="button"
          onClick={() => setAccordionOpen(!accordionOpen)}
          className="w-full px-6 py-4 flex items-center justify-between bg-slate-900/60 hover:bg-slate-900 border-b border-slate-800/80 transition cursor-pointer text-left"
        >
          <div className="flex items-center gap-2.5">
            <FileText className="w-5 h-5 text-cyan-400" />
            <div>
              <h3 className="text-sm font-semibold text-slate-100">
                Clinical Reference: {result.info?.name || classDisplayNames[result.predicted_class]}
              </h3>
              <p className="text-xs text-slate-400">
                Non-prescriptive educational summaries from the knowledge base
              </p>
            </div>
          </div>
          {accordionOpen ? (
            <ChevronUp className="w-5 h-5 text-slate-400" />
          ) : (
            <ChevronDown className="w-5 h-5 text-slate-400" />
          )}
        </button>

        {accordionOpen && result.info && (
          <div className="p-6 space-y-5 text-xs text-slate-300">
            {/* Description */}
            <div>
              <h4 className="text-slate-400 font-mono uppercase tracking-wider text-[11px] mb-1.5">
                Overview & Histological Context
              </h4>
              <p className="leading-relaxed text-slate-200 text-sm bg-slate-900/40 p-3.5 rounded-lg border border-slate-800">
                {result.info.description}
              </p>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-4 pt-2">
              {/* Symptoms */}
              <div className="bg-slate-900/40 border border-slate-800 rounded-lg p-4">
                <h5 className="font-mono text-[11px] text-cyan-300 uppercase tracking-wider mb-2 flex items-center gap-1.5">
                  <Activity className="w-3.5 h-3.5" /> General Symptom Patterns
                </h5>
                <ul className="space-y-1.5 text-slate-300 list-disc list-inside">
                  {result.info.general_symptom_patterns?.map((item, idx) => (
                    <li key={idx} className="leading-normal">
                      {item}
                    </li>
                  ))}
                </ul>
              </div>

              {/* Associated Conditions */}
              <div className="bg-slate-900/40 border border-slate-800 rounded-lg p-4">
                <h5 className="font-mono text-[11px] text-cyan-300 uppercase tracking-wider mb-2 flex items-center gap-1.5">
                  <Layers className="w-3.5 h-3.5" /> Associated Conditions
                </h5>
                <ul className="space-y-1.5 text-slate-300 list-disc list-inside">
                  {result.info.associated_conditions?.map((item, idx) => (
                    <li key={idx} className="leading-normal">
                      {item}
                    </li>
                  ))}
                </ul>
              </div>

              {/* Lifestyle Notes */}
              <div className="bg-slate-900/40 border border-slate-800 rounded-lg p-4">
                <h5 className="font-mono text-[11px] text-cyan-300 uppercase tracking-wider mb-2 flex items-center gap-1.5">
                  <ShieldCheck className="w-3.5 h-3.5" /> General Lifestyle Notes
                </h5>
                <ul className="space-y-1.5 text-slate-300 list-disc list-inside">
                  {result.info.general_lifestyle_notes?.map((item, idx) => (
                    <li key={idx} className="leading-normal">
                      {item}
                    </li>
                  ))}
                </ul>
              </div>
            </div>

            {/* In-Panel Disclaimer */}
            <div className="mt-4 p-3 rounded-lg bg-amber-950/40 border border-amber-500/30 text-amber-200 text-xs flex items-center gap-2.5">
              <AlertTriangle className="w-4 h-4 text-amber-400 shrink-0" />
              <span>
                <strong>Non-Prescriptive Notice:</strong> {result.info.disclaimer || result.disclaimer}
              </span>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};
