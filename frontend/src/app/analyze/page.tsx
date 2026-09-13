"use client";

import React, { useState, useEffect } from "react";
import Link from "next/link";
import { DisclaimerBanner } from "@/components/DisclaimerBanner";
import { Header } from "@/components/Header";
import { UploadSection } from "@/components/UploadSection";
import { ResultsSection } from "@/components/ResultsSection";
import { PredictionResult, BackendHealth } from "@/types";
import { ShieldAlert, AlertCircle, BrainCircuit, Activity, ArrowLeft } from "lucide-react";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export default function AnalyzePage() {
  const [health, setHealth] = useState<BackendHealth | null>(null);
  const [healthError, setHealthError] = useState<boolean>(false);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [originalImageUrl, setOriginalImageUrl] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [result, setResult] = useState<PredictionResult | null>(null);
  const [qualityGateError, setQualityGateError] = useState<string | null>(null);
  const [generalError, setGeneralError] = useState<string | null>(null);

  useEffect(() => {
    const checkHealth = async () => {
      try {
        const res = await fetch(`${API_BASE}/health`);
        if (!res.ok) throw new Error("Health check failed");
        const data = await res.json();
        setHealth(data);
        setHealthError(false);
      } catch {
        setHealthError(true);
      }
    };
    checkHealth();
    const timer = setInterval(checkHealth, 15000);
    return () => clearInterval(timer);
  }, []);

  const handleSelectFile = (file: File | null) => {
    setSelectedFile(file);
    setQualityGateError(null);
    setGeneralError(null);
    if (file) {
      const url = URL.createObjectURL(file);
      setOriginalImageUrl(url);
    } else {
      setOriginalImageUrl(null);
      setResult(null);
    }
  };

  const handleAnalyze = async (file: File) => {
    setIsLoading(true);
    setQualityGateError(null);
    setGeneralError(null);

    const formData = new FormData();
    formData.append("file", file);

    try {
      const res = await fetch(`${API_BASE}/predict`, {
        method: "POST",
        body: formData,
      });

      if (res.status === 422) {
        const errorData = await res.json();
        setQualityGateError(errorData.detail || "Image rejected by MRI Quality Gate.");
        setIsLoading(false);
        return;
      }

      if (!res.ok) {
        const errorData = await res.json().catch(() => ({}));
        throw new Error(errorData.detail || `Inference error: HTTP ${res.status}`);
      }

      const data: PredictionResult = await res.json();
      setResult(data);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Failed to connect to analysis server.";
      setGeneralError(msg);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="flex flex-col min-h-screen bg-[#070b14] clinical-grid">
      {/* 1. Persistent Top Safety Banner */}
      <DisclaimerBanner variant="top" />

      {/* 2. Clinical Header */}
      <Header health={health} healthError={healthError} />

      {/* Navigation subheader */}
      <div className="border-b border-slate-800/80 bg-[#080e1e]/60 px-6 py-2.5">
        <div className="max-w-7xl mx-auto flex items-center justify-between text-xs font-mono">
          <Link
            href="/"
            className="inline-flex items-center gap-1.5 text-slate-400 hover:text-cyan-300 transition"
          >
            <ArrowLeft className="w-3.5 h-3.5" /> Back to System Overview
          </Link>
          <span className="text-slate-400">
            Workstation Mode • Calibrated Inference
          </span>
        </div>
      </div>

      {/* Main Content Area */}
      <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 py-8 space-y-8">
        {/* Research Context Hero */}
        <div className="bg-[#0b1224]/80 border border-slate-800 rounded-2xl p-6 md:p-8 shadow-2xl relative overflow-hidden backdrop-blur-sm">
          <div className="max-w-3xl space-y-3">
            <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-cyan-950/70 border border-cyan-800 text-cyan-300 text-xs font-mono">
              <BrainCircuit className="w-3.5 h-3.5" />
              <span>Diagnostic Workstation • Calibrated T={health?.temperature || 2.0914}</span>
            </div>
            <h1 className="text-2xl sm:text-3xl font-bold text-slate-100 tracking-tight">
              Brain Tumor MRI Saliency & Uncertainty Quantification
            </h1>
            <p className="text-sm text-slate-300 leading-relaxed">
              Upload an axial, coronal, or sagittal T1/T2 MRI brain scan to evaluate class probabilities, 20-pass Monte Carlo Dropout epistemic variance, and Grad-CAM convolutional saliency maps.
            </p>
          </div>
        </div>

        {/* 3. Upload & Quality Screening Section */}
        <UploadSection
          onAnalyze={handleAnalyze}
          isLoading={isLoading}
          selectedFile={selectedFile}
          onSelectFile={handleSelectFile}
        />

        {/* Diagnostic Loading State */}
        {isLoading && (
          <div className="w-full bg-[#0b1224] border border-cyan-800/40 rounded-xl p-8 shadow-2xl text-center space-y-4 animate-pulse">
            <div className="inline-flex p-3 rounded-full bg-cyan-950 border border-cyan-700/50 text-cyan-300">
              <Activity className="w-6 h-6 animate-spin" />
            </div>
            <div>
              <h3 className="text-base font-semibold text-slate-100 font-mono">
                Executing Diagnostic Pipeline
              </h3>
              <p className="text-xs text-slate-400 mt-1 max-w-md mx-auto">
                Screening monochrome quality • Running 20x stochastic MC-Dropout sampling • Scaling logits (T={health?.temperature || 2.0914}) • Generating Grad-CAM activation overlay
              </p>
            </div>
            <div className="max-w-xs mx-auto bg-slate-900 h-1.5 rounded-full overflow-hidden border border-slate-800">
              <div className="h-full bg-gradient-to-r from-cyan-500 to-teal-400 animate-[pulse_1s_infinite] w-full" />
            </div>
          </div>
        )}

        {/* Quality Gate 422 Rejection Banner */}
        {qualityGateError && (
          <div className="w-full bg-amber-950/70 border-2 border-amber-500/60 rounded-xl p-5 shadow-xl flex items-start gap-4">
            <div className="p-2 rounded-lg bg-amber-900/60 text-amber-300 shrink-0">
              <ShieldAlert className="w-6 h-6" />
            </div>
            <div className="space-y-1.5 flex-1 text-left">
              <h3 className="text-sm font-bold text-amber-200 uppercase font-mono tracking-wide">
                Quality Gate Rejection (HTTP 422)
              </h3>
              <p className="text-xs md:text-sm text-amber-200/90 leading-relaxed">
                {qualityGateError}
              </p>
              <p className="text-[11px] text-amber-300/80 font-mono pt-1">
                Diagnostic Safety Requirement: The model strictly expects axial, sagittal, or coronal MRI brain slices with monochrome channel correlation and structured brain parenchyma histograms.
              </p>
            </div>
          </div>
        )}

        {/* General Connection Error */}
        {generalError && (
          <div className="w-full bg-rose-950/60 border border-rose-600/60 rounded-xl p-5 shadow-xl flex items-start gap-4">
            <div className="p-2 rounded-lg bg-rose-900/60 text-rose-300 shrink-0">
              <AlertCircle className="w-6 h-6" />
            </div>
            <div className="space-y-1 flex-1 text-left">
              <h3 className="text-sm font-bold text-rose-200 font-mono uppercase">
                Inference Service Error
              </h3>
              <p className="text-xs md:text-sm text-rose-300/90 leading-relaxed">
                {generalError}
              </p>
              <p className="text-xs text-rose-400 font-mono pt-1">
                Ensure the FastAPI backend is running on http://localhost:8000.
              </p>
            </div>
          </div>
        )}

        {/* 4. Results Section */}
        {result && !isLoading && (
          <ResultsSection
            result={result}
            originalImageUrl={originalImageUrl}
            apiBase={API_BASE}
          />
        )}
      </main>

      {/* 5. Persistent Footer Disclaimer */}
      <DisclaimerBanner variant="footer" />
    </div>
  );
}
