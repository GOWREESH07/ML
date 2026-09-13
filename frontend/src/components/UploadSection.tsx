"use client";

import React, { useState, useRef } from "react";
import { UploadCloud, Image as ImageIcon, X, Sparkles, Check, FileQuestion } from "lucide-react";

interface UploadSectionProps {
  onAnalyze: (file: File) => void;
  isLoading: boolean;
  selectedFile: File | null;
  onSelectFile: (file: File | null) => void;
}

const PRESET_SAMPLES = [
  { id: "glioma", name: "Glioma Sample", file: "glioma.jpg", tag: "Glioma Class" },
  { id: "meningioma", name: "Meningioma Sample", file: "meningioma.jpg", tag: "Meningioma Class" },
  { id: "notumor", name: "Normal Scan", file: "notumor.jpg", tag: "No Tumor" },
  { id: "pituitary", name: "Pituitary Sample", file: "pituitary.jpg", tag: "Pituitary Class" },
];

export const UploadSection: React.FC<UploadSectionProps> = ({
  onAnalyze,
  isLoading,
  selectedFile,
  onSelectFile,
}) => {
  const [dragActive, setDragActive] = useState(false);
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);
  const [loadingSample, setLoadingSample] = useState<string | null>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  const handleFile = (file: File) => {
    if (!file.type.startsWith("image/")) {
      alert("Please upload a valid image file (JPEG or PNG).");
      return;
    }
    onSelectFile(file);
    const url = URL.createObjectURL(file);
    setPreviewUrl(url);
  };

  const handleDrag = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === "dragenter" || e.type === "dragover") {
      setDragActive(true);
    } else if (e.type === "dragleave") {
      setDragActive(false);
    }
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      handleFile(e.dataTransfer.files[0]);
    }
  };

  const handleClear = () => {
    onSelectFile(null);
    if (previewUrl) {
      URL.revokeObjectURL(previewUrl);
    }
    setPreviewUrl(null);
    if (inputRef.current) {
      inputRef.current.value = "";
    }
  };

  const loadPreset = async (filename: string, id: string) => {
    try {
      setLoadingSample(id);
      const res = await fetch(`/samples/${filename}`);
      if (!res.ok) {
        throw new Error("Could not load sample");
      }
      const blob = await res.blob();
      const file = new File([blob], filename, { type: "image/jpeg" });
      handleFile(file);
    } catch (err) {
      console.error("Failed to load preset sample:", err);
    } finally {
      setLoadingSample(null);
    }
  };

  return (
    <div className="w-full bg-[#0b1224] border border-slate-800 rounded-xl p-6 shadow-xl relative overflow-hidden">
      {/* Background flare */}
      <div className="absolute -right-20 -top-20 w-60 h-60 bg-cyan-500/5 rounded-full blur-3xl pointer-events-none" />

      <div className="flex flex-col md:flex-row md:items-center justify-between gap-3 mb-5">
        <div>
          <h2 className="text-base font-semibold text-slate-100 flex items-center gap-2">
            <UploadCloud className="w-5 h-5 text-cyan-400" />
            MRI Image Input & Quality Gate
          </h2>
          <p className="text-xs text-slate-400 mt-0.5">
            Upload an axial, coronal, or sagittal T1/T2-weighted MRI scan. Non-MRI photos will be rejected by the OOD gate.
          </p>
        </div>

        {/* Quick Sample Presets */}
        <div className="flex flex-wrap items-center gap-1.5">
          <span className="text-[11px] font-mono text-slate-400 mr-1 flex items-center gap-1">
            <Sparkles className="w-3 h-3 text-cyan-400" /> Test Presets:
          </span>
          {PRESET_SAMPLES.map((sample) => (
            <button
              key={sample.id}
              type="button"
              disabled={isLoading || loadingSample === sample.id}
              onClick={() => loadPreset(sample.file, sample.id)}
              className="text-[11px] px-2.5 py-1 rounded bg-slate-900 border border-slate-700 hover:border-cyan-500/60 hover:bg-slate-800 text-slate-300 transition flex items-center gap-1 font-mono disabled:opacity-50 cursor-pointer"
            >
              {loadingSample === sample.id ? (
                <span className="w-2.5 h-2.5 border-2 border-cyan-400 border-t-transparent rounded-full animate-spin" />
              ) : (
                <span>{sample.name.split(" ")[0]}</span>
              )}
            </button>
          ))}
        </div>
      </div>

      {/* Main Upload Zone */}
      {!previewUrl ? (
        <div
          onDragEnter={handleDrag}
          onDragLeave={handleDrag}
          onDragOver={handleDrag}
          onDrop={handleDrop}
          onClick={() => inputRef.current?.click()}
          className={`border-2 border-dashed rounded-xl p-8 transition-all flex flex-col items-center justify-center text-center cursor-pointer min-h-[220px] ${
            dragActive
              ? "border-cyan-400 bg-cyan-950/20"
              : "border-slate-800 hover:border-slate-700 bg-slate-900/40 hover:bg-slate-900/60"
          }`}
        >
          <input
            ref={inputRef}
            type="file"
            accept="image/png, image/jpeg, image/jpg"
            className="hidden"
            onChange={(e) => {
              if (e.target.files && e.target.files[0]) {
                handleFile(e.target.files[0]);
              }
            }}
          />
          <div className="w-12 h-12 rounded-full bg-slate-800/80 border border-slate-700 flex items-center justify-center text-cyan-400 mb-3 shadow-inner">
            <UploadCloud className="w-6 h-6" />
          </div>
          <p className="text-sm font-medium text-slate-200">
            Drag and drop MRI scan image here, or{" "}
            <span className="text-cyan-400 hover:underline">browse files</span>
          </p>
          <p className="text-xs text-slate-400 mt-1">
            Supported formats: DICOM exports, PNG, JPEG (Grayscale MRI brain slice)
          </p>
          <div className="mt-4 flex items-center gap-4 text-[11px] text-slate-400 font-mono">
            <span className="flex items-center gap-1">
              <Check className="w-3 h-3 text-cyan-400" /> Channel Check
            </span>
            <span className="flex items-center gap-1">
              <Check className="w-3 h-3 text-cyan-400" /> Histogram Spread
            </span>
            <span className="flex items-center gap-1">
              <Check className="w-3 h-3 text-cyan-400" /> Otsu Extent
            </span>
          </div>
        </div>
      ) : (
        /* Preview State */
        <div className="bg-slate-900/70 border border-slate-800 rounded-xl p-4 flex flex-col sm:flex-row items-center gap-5">
          <div className="relative w-36 h-36 bg-black rounded-lg border border-slate-700 overflow-hidden shrink-0 flex items-center justify-center">
            {/* eslint-disable-next-line @next/next/no-img-element */}
            <img
              src={previewUrl}
              alt="Scan Preview"
              className="max-h-full max-w-full object-contain"
            />
            <button
              onClick={handleClear}
              type="button"
              disabled={isLoading}
              className="absolute top-1.5 right-1.5 p-1 rounded-full bg-slate-900/80 text-slate-300 hover:text-white hover:bg-rose-900/80 transition"
              title="Remove image"
            >
              <X className="w-3.5 h-3.5" />
            </button>
          </div>

          <div className="flex-1 text-left w-full">
            <div className="flex items-center gap-2">
              <span className="text-xs font-mono uppercase px-2 py-0.5 rounded bg-cyan-950 border border-cyan-800 text-cyan-300">
                Ready for Analysis
              </span>
              <span className="text-xs text-slate-400 font-mono">
                {selectedFile?.name}
              </span>
            </div>
            <p className="text-xs text-slate-400 mt-2">
              File size: {(Number(selectedFile?.size || 0) / 1024).toFixed(1)} KB • Type: {selectedFile?.type || "image/jpeg"}
            </p>
            <p className="text-xs text-slate-400 mt-1">
              The scan will pass through the automated quality gate before executing 20 stochastic MC-Dropout passes and Grad-CAM extraction.
            </p>

            <div className="mt-4 flex items-center gap-3">
              <button
                type="button"
                disabled={isLoading}
                onClick={() => selectedFile && onAnalyze(selectedFile)}
                className="px-5 py-2 rounded-lg bg-cyan-600 hover:bg-cyan-500 text-slate-950 font-semibold text-xs transition flex items-center gap-2 shadow-lg shadow-cyan-600/20 cursor-pointer disabled:opacity-50"
              >
                {isLoading ? (
                  <>
                    <span className="w-3.5 h-3.5 border-2 border-slate-950 border-t-transparent rounded-full animate-spin" />
                    Analyzing Scan (20x MC-Dropout)...
                  </>
                ) : (
                  <>
                    <Sparkles className="w-3.5 h-3.5" />
                    Execute MRI Diagnostic Analysis
                  </>
                )}
              </button>

              <button
                type="button"
                disabled={isLoading}
                onClick={handleClear}
                className="px-3 py-2 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs transition cursor-pointer"
              >
                Clear / Replace
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
