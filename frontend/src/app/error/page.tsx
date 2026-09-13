"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";

export default function ErrorRedirect() {
  const router = useRouter();

  useEffect(() => {
    router.replace("/");
  }, [router]);

  return (
    <div className="flex items-center justify-center min-h-screen bg-[#070b14] text-slate-300">
      <div className="text-center space-y-2">
        <div className="w-8 h-8 border-2 border-cyan-400 border-t-transparent rounded-full animate-spin mx-auto" />
        <p className="text-sm font-mono">Redirecting to NeuroScan AI Workstation...</p>
      </div>
    </div>
  );
}
