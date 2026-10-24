import React, { useState } from "react";
import { DocumentModel } from "../models";
import {
  FileText,
  Trash2,
  Layers,
  MessageSquare,
  Search,
  BookOpen,
  Eye,
  CheckCircle,
} from "lucide-react";

interface DocumentListProps {
  documents: DocumentModel[];
  loading: boolean;
  selectedDocId: string | null;
  onSelectDoc: (id: string | null) => void;
  onInspectDoc: (id: string) => void;
  onDeleteDoc: (id: string) => Promise<boolean>;
}

export const DocumentList: React.FC<DocumentListProps> = ({
  documents,
  loading,
  selectedDocId,
  onSelectDoc,
  onInspectDoc,
  onDeleteDoc,
}) => {
  const [searchTerm, setSearchTerm] = useState("");
  const [deletingId, setDeletingId] = useState<string | null>(null);

  const filteredDocs = documents.filter((doc) =>
    doc.filename.toLowerCase().includes(searchTerm.toLowerCase())
  );

  const handleDelete = async (e: React.MouseEvent, doc: DocumentModel) => {
    e.stopPropagation();
    if (window.confirm(`Delete '${doc.filename}' and all its indexed chunks from ChromaDB?`)) {
      setDeletingId(doc.id);
      await onDeleteDoc(doc.id);
      setDeletingId(null);
      if (selectedDocId === doc.id) {
        onSelectDoc(null);
      }
    }
  };

  return (
    <div className="document-list-container">
      <div className="document-list-header">
        <div className="flex items-center gap-2">
          <BookOpen size={16} className="text-indigo-600" />
          <h3 className="font-semibold text-sm text-slate-800">
            Ingested Documents ({documents.length})
          </h3>
        </div>

        {documents.length > 3 && (
          <div className="search-bar">
            <Search size={13} className="text-slate-400" />
            <input
              type="text"
              placeholder="Filter files..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="search-input"
            />
          </div>
        )}
      </div>

      {loading && documents.length === 0 ? (
        <div className="empty-state">
          <p className="text-xs text-slate-400">Loading documents...</p>
        </div>
      ) : documents.length === 0 ? (
        <div className="empty-state">
          <FileText size={32} className="text-slate-300 mb-2" />
          <p className="text-sm font-medium text-slate-600">No documents indexed yet</p>
          <p className="text-xs text-slate-400 mt-1">
            Upload a PDF, Markdown, or Text file above to start querying.
          </p>
        </div>
      ) : (
        <div className="doc-cards-list">
          {filteredDocs.map((doc) => {
            const isSelected = selectedDocId === doc.id;
            const badge = doc.getFormatBadge();

            return (
              <div
                key={doc.id}
                className={`doc-card ${isSelected ? "selected" : ""}`}
                onClick={() => onSelectDoc(isSelected ? null : doc.id)}
              >
                <div className="doc-card-main">
                  <div className="doc-card-icon" style={{ backgroundColor: badge.bg, color: badge.color }}>
                    <FileText size={18} />
                  </div>

                  <div className="doc-card-info">
                    <div className="flex items-center gap-2">
                      <span className="doc-filename" title={doc.filename}>
                        {doc.filename}
                      </span>
                      <span
                        className="format-tag"
                        style={{ color: badge.color, backgroundColor: badge.bg }}
                      >
                        {badge.label}
                      </span>
                    </div>

                    <div className="doc-meta-row">
                      <span>{doc.getFormattedSize()}</span>
                      <span>&bull;</span>
                      <span className="flex items-center gap-1">
                        <Layers size={11} /> {doc.chunkCount} chunks
                      </span>
                      {doc.pageCount && (
                        <>
                          <span>&bull;</span>
                          <span>{doc.pageCount} pages</span>
                        </>
                      )}
                      <span>&bull;</span>
                      <span>{doc.getFormattedDate()}</span>
                    </div>
                  </div>
                </div>

                <div className="doc-card-actions">
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      onSelectDoc(isSelected ? null : doc.id);
                    }}
                    className={`btn-action-scope ${isSelected ? "active" : ""}`}
                    title={isSelected ? "Currently active for queries (click to unscope)" : "Scope queries to this document"}
                  >
                    {isSelected ? (
                      <>
                        <CheckCircle size={13} className="text-indigo-600" />
                        <span>Active</span>
                      </>
                    ) : (
                      <>
                        <MessageSquare size={13} />
                        <span>Ask</span>
                      </>
                    )}
                  </button>

                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      onInspectDoc(doc.id);
                    }}
                    className="btn-action-icon"
                    title="Inspect Chunks in ChromaDB"
                  >
                    <Eye size={14} />
                  </button>

                  <button
                    onClick={(e) => handleDelete(e, doc)}
                    className="btn-action-icon delete"
                    disabled={deletingId === doc.id}
                    title="Delete document and chunks"
                  >
                    <Trash2 size={14} />
                  </button>
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
};
