import React from "react";
import { AlertTriangle, ShieldAlert } from "lucide-react";

interface DisclaimerBannerProps {
  variant?: "top" | "inline" | "footer";
}

export const DisclaimerBanner: React.FC<DisclaimerBannerProps> = ({ variant = "top" }) => {
  if (variant === "footer") {
    return (
      <footer className="mt-16 border-t border-slate-800/80 bg-[#090e1c] py-6 px-4 text-slate-400">
        <div className="max-w-7xl mx-auto flex flex-col md:flex-row items-center justify-between gap-4 text-xs">
          <div className="flex items-center gap-2 text-slate-400">
            <ShieldAlert className="w-4 h-4 text-cyan-400 shrink-0" />
            <span>
              <strong>Clinical Research Disclaimer:</strong> This system is not a medical device. Always consult a qualified board-certified neurologist or oncologist for diagnosis.
            </span>
          </div>
          <div className="text-slate-400 text-right">
            <span>NeuroScan AI • PyTorch MC-Dropout & Grad-CAM Research Pipeline</span>
          </div>
        </div>
      </footer>
    );
  }

  return (
    <div className="w-full bg-slate-900/95 border-b border-amber-500/30 px-4 py-2.5 backdrop-blur-md sticky top-0 z-50 shadow-lg shadow-black/40">
      <div className="max-w-7xl mx-auto flex items-center justify-between gap-3 text-xs md:text-sm">
        <div className="flex items-center gap-2.5 text-amber-200">
          <AlertTriangle className="w-4 h-4 text-amber-400 shrink-0 animate-pulse" />
          <p className="font-medium tracking-wide">
            <span className="font-semibold text-amber-300 uppercase tracking-wider text-[11px] mr-1.5 px-1.5 py-0.5 rounded bg-amber-950/60 border border-amber-500/30">
              Research Prototype
            </span>
            This tool is for research & educational demonstration only. Not certified for medical diagnosis or clinical treatment planning.
          </p>
        </div>
        <div className="hidden lg:flex items-center gap-1.5 text-slate-400 text-xs shrink-0 font-mono">
          <span className="w-2 h-2 rounded-full bg-emerald-400 inline-block animate-ping" />
          <span>Non-Dismissible Safety Policy</span>
        </div>
      </div>
    </div>
  );
};
