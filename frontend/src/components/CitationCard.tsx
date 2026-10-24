import React, { useState } from "react";
import { CitationModel } from "../models";
import { ChevronRight, FileText, Bookmark } from "lucide-react";

interface CitationCardProps {
  citation: CitationModel;
  index: number;
}

export const CitationCard: React.FC<CitationCardProps> = ({ citation, index }) => {
  const [expanded, setExpanded] = useState(false);
  const color = citation.getConfidenceColor();

  return (
    <div className="citation-card" onClick={() => setExpanded(!expanded)}>
      <div className="citation-card-header">
        <div className="flex items-center gap-2">
          <span className="citation-num">[{index + 1}]</span>
          <FileText size={13} className="text-slate-500" />
          <span className="citation-filename font-medium text-xs text-slate-800" title={citation.filename}>
            {citation.filename}
          </span>
          <span className="citation-page-pill text-[11px] text-slate-500">
            {citation.getPageLabel()}
          </span>
        </div>

        <div className="flex items-center gap-2">
          <span
            className="citation-score-badge"
            style={{ color: color.text, backgroundColor: color.bg, borderColor: color.border }}
          >
            {citation.getConfidencePercentage()}
          </span>
          <ChevronRight size={13} className={`text-slate-400 transition-transform ${expanded ? "rotate-90" : ""}`} />
        </div>
      </div>

      <div className={`citation-body ${expanded ? "expanded" : "collapsed"}`}>
        <p className="citation-snippet text-xs text-slate-600 leading-relaxed bg-slate-50 p-2.5 rounded border border-slate-100">
          &ldquo;{citation.snippet}&rdquo;
        </p>
        <div className="citation-footer text-[10px] text-slate-400 mt-1 flex items-center justify-between">
          <span className="font-mono flex items-center gap-1">
            <Bookmark size={10} /> ID: {citation.chunkId}
          </span>
        </div>
      </div>
    </div>
  );
};
