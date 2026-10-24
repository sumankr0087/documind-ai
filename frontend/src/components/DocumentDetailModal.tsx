import React from "react";
import { DocumentModel, ChunkModel } from "../models";
import { X, Layers, Hash, FileText } from "lucide-react";

interface DocumentDetailModalProps {
  data: {
    document: DocumentModel;
    chunks: ChunkModel[];
  } | null;
  loading: boolean;
  onClose: () => void;
}

export const DocumentDetailModal: React.FC<DocumentDetailModalProps> = ({ data, loading, onClose }) => {
  if (!data && !loading) return null;

  return (
    <div className="modal-backdrop" onClick={onClose}>
      <div className="modal-card" onClick={(e) => e.stopPropagation()}>
        <div className="modal-header">
          <div>
            <h3 className="modal-title font-semibold text-base text-slate-800">
              {data?.document.filename || "Loading..."}
            </h3>
            <p className="modal-subtitle text-xs text-slate-400 mt-0.5">
              Document ID: <span className="font-mono">{data?.document.id}</span>
            </p>
          </div>
          <button onClick={onClose} className="modal-close-btn">
            <X size={18} />
          </button>
        </div>

        {loading ? (
          <div className="p-8 text-center text-sm text-slate-500">Loading chunk details...</div>
        ) : (
          <div className="modal-content">
            <div className="doc-stats-grid">
              <div className="stat-box">
                <span className="stat-label">Total Chunks</span>
                <span className="stat-value">{data?.chunks.length}</span>
              </div>
              <div className="stat-box">
                <span className="stat-label">File Size</span>
                <span className="stat-value">{data?.document.getFormattedSize()}</span>
              </div>
              <div className="stat-box">
                <span className="stat-label">Type</span>
                <span className="stat-value uppercase">{data?.document.getExtension()}</span>
              </div>
              <div className="stat-box">
                <span className="stat-label">Pages</span>
                <span className="stat-value">{data?.document.pageCount ?? "N/A"}</span>
              </div>
            </div>

            <h4 className="font-semibold text-xs text-slate-500 uppercase tracking-wider mb-2 mt-4 flex items-center gap-1.5">
              <Layers size={13} />
              Constituent Text Chunks in ChromaDB
            </h4>

            <div className="chunks-list">
              {data?.chunks.map((chunk) => (
                <div key={chunk.chunkId} className="chunk-card">
                  <div className="chunk-header">
                    <span className="chunk-badge">
                      <Hash size={10} /> Chunk #{chunk.chunkIndex}
                    </span>
                    <span className="chunk-page">
                      <FileText size={10} /> {chunk.getPageLabel()}
                    </span>
                    <span className="chunk-len text-slate-400 text-xs">
                      {chunk.charLength} chars
                    </span>
                  </div>
                  <div className="chunk-id font-mono text-[10px] text-slate-400 mb-1">
                    {chunk.chunkId}
                  </div>
                  {chunk.text ? (
                    <p className="chunk-text text-xs text-slate-700 leading-relaxed font-sans bg-slate-50 p-2.5 rounded border border-slate-100">
                      {chunk.text}
                    </p>
                  ) : (
                    <p className="chunk-placeholder text-xs text-slate-400 italic">
                      Indexed vector chunk with source metadata.
                    </p>
                  )}
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
};
