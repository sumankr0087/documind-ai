import React, { useState } from "react";
import { SystemHealthModel } from "../models";
import { Activity, Database, Cpu, Sparkles, ChevronDown, CheckCircle2, AlertCircle } from "lucide-react";

interface SystemHealthBadgeProps {
  health: SystemHealthModel | null;
  loading: boolean;
  onRefresh: () => void;
}

export const SystemHealthBadge: React.FC<SystemHealthBadgeProps> = ({ health, loading, onRefresh }) => {
  const [isOpen, setIsOpen] = useState(false);

  if (loading && !health) {
    return (
      <div className="status-pill loading">
        <Activity className="spin-icon" size={14} />
        <span>Connecting...</span>
      </div>
    );
  }

  const isHealthy = health?.isHealthy() ?? false;

  return (
    <div className="relative">
      <button
        onClick={() => setIsOpen(!isOpen)}
        className={`status-pill ${isHealthy ? "healthy" : "degraded"}`}
        title="Click to view detailed system health"
      >
        <span className={`status-dot ${isHealthy ? "healthy" : "degraded"}`} />
        <span className="font-medium text-xs">
          {isHealthy ? "System Ready" : "Degraded / Offline"}
        </span>
        <ChevronDown size={13} className={`transition-transform ${isOpen ? "rotate-180" : ""}`} />
      </button>

      {isOpen && (
        <div className="health-popover">
          <div className="popover-header">
            <div className="flex items-center gap-2">
              {isHealthy ? (
                <CheckCircle2 size={16} className="text-emerald-500" />
              ) : (
                <AlertCircle size={16} className="text-amber-500" />
              )}
              <h4 className="font-semibold text-sm">System Diagnostics</h4>
            </div>
            <button onClick={onRefresh} className="refresh-btn text-xs">
              Refresh
            </button>
          </div>

          <div className="popover-body">
            <div className="diag-item">
              <div className="diag-label">
                <Database size={14} className="text-indigo-400" />
                <span>ChromaDB Vector Store</span>
              </div>
              <span className={`diag-value ${health?.vectorStoreConnected ? "text-emerald-600" : "text-amber-600"}`}>
                {health?.vectorStoreStatus} ({health?.totalChunks ?? 0} chunks)
              </span>
            </div>

            <div className="diag-item">
              <div className="diag-label">
                <Cpu size={14} className="text-sky-400" />
                <span>Embedding Model</span>
              </div>
              <span className="diag-value font-mono text-xs">
                {health?.embeddingModel ? health.embeddingModel.split("/").pop() : "all-MiniLM-L6-v2"} ({health?.embeddingDevice})
              </span>
            </div>

            <div className="diag-item">
              <div className="diag-label">
                <Sparkles size={14} className="text-violet-400" />
                <span>LLM Generation</span>
              </div>
              <span className="diag-value">
                {health?.llmProvider.toUpperCase()} ({health?.llmModel})
              </span>
            </div>

            <div className="diag-item text-xs text-slate-400 pt-1 border-t border-slate-100">
              <span>Environment: {health?.appEnv} (v{health?.version})</span>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
