import React from "react";
import { Activity, Brain, Server, CheckCircle2, AlertCircle } from "lucide-react";
import { BackendHealth } from "@/types";

interface HeaderProps {
  health: BackendHealth | null;
  healthError: boolean;
}

export const Header: React.FC<HeaderProps> = ({ health, healthError }) => {
  return (
    <header className="border-b border-slate-800 bg-[#090f20]/90 backdrop-blur-md px-6 py-4">
      <div className="max-w-7xl mx-auto flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        {/* Brand identity */}
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-lg bg-gradient-to-br from-cyan-500/20 to-teal-500/10 border border-cyan-500/30 flex items-center justify-center text-cyan-400 shadow-inner">
            <Brain className="w-5 h-5" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h1 className="font-semibold text-lg text-slate-100 tracking-tight">
                NeuroScan <span className="text-cyan-400 font-mono text-sm uppercase">AI</span>
              </h1>
              <span className="text-[10px] font-mono uppercase px-2 py-0.5 rounded-full bg-cyan-950/70 border border-cyan-800 text-cyan-300">
                v1.0.0
              </span>
            </div>
            <p className="text-xs text-slate-400">
              Brain MRI Classification • MC-Dropout Uncertainty • Grad-CAM Saliency
            </p>
          </div>
        </div>

        {/* Backend & Architecture Status */}
        <div className="flex items-center gap-3 text-xs">
          <div className="flex items-center gap-2 bg-slate-900/80 border border-slate-800 rounded-md px-3 py-1.5 font-mono">
            <Server className="w-3.5 h-3.5 text-slate-400" />
            <span className="text-slate-400">Backend:</span>
            {healthError ? (
              <span className="flex items-center gap-1 text-rose-400">
                <AlertCircle className="w-3 h-3" /> Offline (localhost:8000)
              </span>
            ) : health?.model_loaded ? (
              <span className="flex items-center gap-1 text-emerald-400">
                <CheckCircle2 className="w-3 h-3" /> Live (4 Classes)
              </span>
            ) : (
              <span className="flex items-center gap-1 text-amber-400">
                <Activity className="w-3 h-3 animate-spin" /> Connecting...
              </span>
            )}
          </div>

          <div className="hidden md:flex items-center gap-2 bg-slate-900/80 border border-slate-800 rounded-md px-3 py-1.5 font-mono text-slate-400">
            <span>Passes:</span>
            <span className="text-cyan-300">20x MC-Dropout</span>
          </div>
        </div>
      </div>
    </header>
  );
};
