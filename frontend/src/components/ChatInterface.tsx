import React, { useState, useRef, useEffect } from "react";
import { QAMessageModel, DocumentModel } from "../models";
import { CitationCard } from "./CitationCard";
import {
  Send,
  Loader2,
  Trash2,
  SlidersHorizontal,
  Bot,
  User,
  AlertTriangle,
  Sparkles,
  BookMarked,
  Filter,
} from "lucide-react";

interface ChatInterfaceProps {
  messages: QAMessageModel[];
  isAsking: boolean;
  documents: DocumentModel[];
  selectedDocId: string | null;
  onSelectDoc: (id: string | null) => void;
  topK: number;
  onTopKChange: (k: number) => void;
  onAsk: (question: string) => void;
  onClear: () => void;
}

const SAMPLE_QUESTIONS = [
  "What are the main components of this document?",
  "Summarize the key architectural decisions and findings.",
  "What security or deployment measures are recommended?",
  "What tools and libraries are specified for retrieval?",
];

export const ChatInterface: React.FC<ChatInterfaceProps> = ({
  messages,
  isAsking,
  documents,
  selectedDocId,
  onSelectDoc,
  topK,
  onTopKChange,
  onAsk,
  onClear,
}) => {
  const [input, setInput] = useState("");
  const [showSettings, setShowSettings] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, isAsking]);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim() || isAsking) return;
    onAsk(input);
    setInput("");
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSubmit(e);
    }
  };

  const selectedDoc = documents.find((d) => d.id === selectedDocId);

  return (
    <div className="chat-container">
      {/* Chat Sub-Header / Scoping & Settings Bar */}
      <div className="chat-header-bar">
        <div className="flex items-center gap-2 flex-wrap flex-1">
          <div className="scoping-dropdown-wrapper">
            <Filter size={13} className="text-slate-500" />
            <select
              value={selectedDocId || ""}
              onChange={(e) => onSelectDoc(e.target.value || null)}
              className="scoping-select"
            >
              <option value="">Query All Documents ({documents.length})</option>
              {documents.map((doc) => (
                <option key={doc.id} value={doc.id}>
                  Scope: {doc.filename}
                </option>
              ))}
            </select>
          </div>

          {selectedDoc && (
            <span className="scoped-active-tag">
              Scoped to {selectedDoc.filename}
              <button onClick={() => onSelectDoc(null)} className="ml-1 text-indigo-400 hover:text-indigo-600">
                &times;
              </button>
            </span>
          )}
        </div>

        <div className="flex items-center gap-2">
          <button
            onClick={() => setShowSettings(!showSettings)}
            className={`btn-icon-subtle ${showSettings ? "active" : ""}`}
            title="Retrieval configuration (Top-K)"
          >
            <SlidersHorizontal size={14} />
            <span className="text-xs">Top-K: {topK}</span>
          </button>

          {messages.length > 0 && (
            <button onClick={onClear} className="btn-icon-subtle text-slate-400 hover:text-red-500" title="Clear thread">
              <Trash2 size={14} />
            </button>
          )}
        </div>
      </div>

      {/* Top-K Settings Slideout */}
      {showSettings && (
        <div className="topk-settings-panel">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold text-slate-700">Top-K Context Chunks Retrieved:</span>
            <span className="text-xs font-mono font-bold text-indigo-600 bg-indigo-50 px-2 py-0.5 rounded">
              {topK}
            </span>
          </div>
          <input
            type="range"
            min={1}
            max={10}
            step={1}
            value={topK}
            onChange={(e) => onTopKChange(Number(e.target.value))}
            className="w-full mt-2 accent-indigo-600 cursor-pointer"
          />
          <div className="flex justify-between text-[10px] text-slate-400 mt-1">
            <span>1 (Precise)</span>
            <span>5 (Balanced Default)</span>
            <span>10 (Broad)</span>
          </div>
        </div>
      )}

      {/* Message Thread */}
      <div className="chat-messages-area">
        {messages.length === 0 ? (
          <div className="chat-empty-state">
            <div className="chat-empty-icon">
              <Sparkles size={28} className="text-indigo-500" />
            </div>
            <h3 className="font-semibold text-base text-slate-800 mt-3">
              Ask anything grounded in your documents
            </h3>
            <p className="text-xs text-slate-500 max-w-md text-center mt-1">
              DocuMind AI embeds your question, retrieves the highest-similarity chunks with ChromaDB, and generates an objective answer backed by verifiable citations.
            </p>

            <div className="sample-questions-grid mt-6">
              <span className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider mb-1 w-full text-left">
                Suggested Questions:
              </span>
              {SAMPLE_QUESTIONS.map((q, idx) => (
                <button key={idx} onClick={() => onAsk(q)} className="sample-q-btn">
                  <span>&ldquo;{q}&rdquo;</span>
                </button>
              ))}
            </div>
          </div>
        ) : (
          <div className="messages-list">
            {messages.map((msg) => (
              <div key={msg.id} className={`message-row ${msg.sender}`}>
                <div className="message-avatar">
                  {msg.sender === "user" ? (
                    <User size={16} className="text-white" />
                  ) : (
                    <Bot size={16} className="text-indigo-600" />
                  )}
                </div>

                <div className="message-content-wrapper">
                  <div className="message-bubble">
                    <p className="message-text">{msg.text}</p>
                  </div>

                  {/* Insufficient Evidence Warning Banner */}
                  {msg.isInsufficientEvidence() && (
                    <div className="insufficient-evidence-alert">
                      <AlertTriangle size={14} className="text-amber-500 shrink-0" />
                      <div>
                        <span className="font-semibold text-amber-800 text-xs">Insufficient Evidence in Scope: </span>
                        <span className="text-amber-700 text-xs">
                          The indexed documents do not contain high-confidence data for this question. No fabricated facts were generated.
                        </span>
                      </div>
                    </div>
                  )}

                  {/* Citations List */}
                  {msg.hasCitations() && (
                    <div className="citations-container">
                      <div className="citations-header">
                        <BookMarked size={12} className="text-indigo-500" />
                        <span className="font-semibold text-xs text-slate-600">
                          Verified Source Citations ({msg.citations.length})
                        </span>
                      </div>
                      <div className="citations-grid">
                        {msg.citations.map((c, idx) => (
                          <CitationCard key={c.chunkId} citation={c} index={idx} />
                        ))}
                      </div>
                    </div>
                  )}

                  {msg.modelUsed && (
                    <div className="message-footer-meta">
                      <span>Engine: {msg.modelUsed}</span>
                    </div>
                  )}
                </div>
              </div>
            ))}

            {isAsking && (
              <div className="message-row assistant">
                <div className="message-avatar">
                  <Bot size={16} className="text-indigo-600" />
                </div>
                <div className="message-content-wrapper">
                  <div className="message-bubble loading">
                    <Loader2 size={16} className="spin-icon text-indigo-600" />
                    <span className="text-xs text-slate-500">Retrieving chunks and formulating grounded answer...</span>
                  </div>
                </div>
              </div>
            )}

            <div ref={messagesEndRef} />
          </div>
        )}
      </div>

      {/* Chat Input Box */}
      <div className="chat-input-area">
        <form onSubmit={handleSubmit} className="chat-form">
          <textarea
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder={
              selectedDoc
                ? `Ask question about "${selectedDoc.filename}" (Press Enter to send)...`
                : "Ask questions across all ingested documents (Press Enter to send)..."
            }
            rows={1}
            className="chat-textarea"
            disabled={isAsking}
          />
          <button type="submit" disabled={!input.trim() || isAsking} className="btn-send">
            {isAsking ? <Loader2 size={16} className="spin-icon" /> : <Send size={16} />}
          </button>
        </form>
        <div className="input-hint">
          <span>Press <strong>Enter</strong> to send &bull; <strong>Shift + Enter</strong> for newline</span>
        </div>
      </div>
    </div>
  );
};
