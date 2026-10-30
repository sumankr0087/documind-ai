import React, { useState, useRef, useEffect } from "react";
import { QAMessageModel, DocumentModel, ChatSessionModel } from "../models";
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
  PlusCircle,
  MessageSquare,
  FileCheck,
  CheckSquare,
  Square,
  Layers,
  FileText,
  ChevronLeft,
  ChevronRight,
} from "lucide-react";

interface ChatInterfaceProps {
  messages: QAMessageModel[];
  isAsking: boolean;
  streamingDelta?: string;
  documents: DocumentModel[];
  selectedDocIds: string[];
  onToggleDoc: (id: string) => void;
  onClearDocSelection: () => void;
  topK: number;
  onTopKChange: (k: number) => void;
  enableMmr: boolean;
  onToggleMmr: (val: boolean) => void;
  enableHybrid: boolean;
  onToggleHybrid: (val: boolean) => void;
  enableReranking: boolean;
  onToggleReranking: (val: boolean) => void;
  sessions: ChatSessionModel[];
  activeSessionId: string | null;
  onSelectSession: (id: string) => void;
  onCreateSession: () => void;
  onDeleteSession: (id: string) => void;
  onAsk: (question: string) => void;
  onClear: () => void;
}

const SAMPLE_QUESTIONS = [
  "What are the main components and key points in this document?",
  "Summarize the technical background and key findings.",
  "What tools, libraries, or credentials are required?",
  "What security guidelines or recommendations are specified?",
];

export const ChatInterface: React.FC<ChatInterfaceProps> = ({
  messages,
  isAsking,
  streamingDelta = "",
  documents,
  selectedDocIds,
  onToggleDoc,
  onClearDocSelection,
  topK,
  onTopKChange,
  enableMmr,
  onToggleMmr,
  enableHybrid,
  onToggleHybrid,
  enableReranking,
  onToggleReranking,
  sessions,
  activeSessionId,
  onSelectSession,
  onCreateSession,
  onDeleteSession,
  onAsk,
  onClear,
}) => {
  const [input, setInput] = useState("");
  const [showSettings, setShowSettings] = useState(false);
  const [showDocSelector, setShowDocSelector] = useState(false);
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, isAsking, streamingDelta]);

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

  const selectedDocs = documents.filter((d) => selectedDocIds.includes(d.id));

  return (
    <div className="chat-layout-wrapper">
      {/* 1. Topics Sidebar */}
      <aside className={`topics-sidebar ${sidebarOpen ? "" : "collapsed"}`}>
        <div className="topics-header">
          {sidebarOpen ? (
            <>
              <button onClick={onCreateSession} className="btn-new-topic" title="Start new conversation topic">
                <PlusCircle size={14} />
                <span>New Topic</span>
              </button>
              <button
                onClick={() => setSidebarOpen(false)}
                className="btn-sidebar-toggle"
                title="Collapse sidebar"
              >
                <ChevronLeft size={16} />
              </button>
            </>
          ) : (
            <button
              onClick={() => setSidebarOpen(true)}
              className="btn-sidebar-toggle"
              style={{ margin: "0 auto" }}
              title="Expand topics sidebar"
            >
              <ChevronRight size={16} />
            </button>
          )}
        </div>

        {sidebarOpen && (
          <div className="topics-list">
            <div className="topics-section-title">
              Chat Topics ({sessions.length})
            </div>
            {sessions.length === 0 ? (
              <div style={{ fontSize: "12px", color: "var(--slate-500)", padding: "12px 8px", textAlign: "center" }}>
                No saved topics yet. Start chatting to save your conversation in SQLite.
              </div>
            ) : (
              sessions.map((s) => (
                <div
                  key={s.sessionId}
                  onClick={() => onSelectSession(s.sessionId)}
                  className={`topic-item ${activeSessionId === s.sessionId ? "active" : ""}`}
                >
                  <div className="topic-title-wrapper">
                    <MessageSquare size={13} style={{ flexShrink: 0 }} />
                    <span style={{ overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
                      {s.title}
                    </span>
                  </div>
                  <div style={{ display: "flex", alignItems: "center", gap: "6px" }}>
                    <span style={{ fontSize: "10px", opacity: 0.7 }}>{s.messageCount}</span>
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        onDeleteSession(s.sessionId);
                      }}
                      className="topic-delete-btn"
                      title="Delete topic"
                    >
                      <Trash2 size={12} />
                    </button>
                  </div>
                </div>
              ))
            )}
          </div>
        )}
      </aside>

      {/* 2. Main Chat Conversation Area */}
      <div className="chat-main-view">
        {/* Top Control Bar: Document Selection & Retrieval Toggles */}
        <div className="chat-toolbar">
          <div className="toolbar-left">
            {/* Multi-document scope button */}
            <div style={{ position: "relative" }}>
              <button
                onClick={() => setShowDocSelector(!showDocSelector)}
                className={`btn-scope-filter ${selectedDocIds.length > 0 ? "active" : ""}`}
              >
                <Filter size={13} />
                <span>
                  {selectedDocIds.length === 0
                    ? `Searching All Documents (${documents.length})`
                    : `Scoped to ${selectedDocIds.length} Document(s)`}
                </span>
              </button>

              {/* Document selection dropdown */}
              {showDocSelector && (
                <div className="scope-dropdown-menu">
                  <div className="scope-dropdown-header">
                    <span>Select Search Scope:</span>
                    {selectedDocIds.length > 0 && (
                      <button
                        onClick={onClearDocSelection}
                        style={{ background: "transparent", border: "none", color: "var(--primary)", fontSize: "11px", cursor: "pointer", fontWeight: 600 }}
                      >
                        Reset to All
                      </button>
                    )}
                  </div>
                  <div className="scope-dropdown-list">
                    {documents.length === 0 ? (
                      <p style={{ fontSize: "12px", color: "var(--slate-400)", padding: "8px", textAlign: "center" }}>
                        No documents uploaded yet.
                      </p>
                    ) : (
                      documents.map((doc) => {
                        const isChecked = selectedDocIds.includes(doc.id);
                        return (
                          <div
                            key={doc.id}
                            onClick={() => onToggleDoc(doc.id)}
                            className="scope-doc-item"
                          >
                            {isChecked ? (
                              <CheckSquare size={14} style={{ color: "var(--primary)", flexShrink: 0 }} />
                            ) : (
                              <Square size={14} style={{ color: "var(--slate-300)", flexShrink: 0 }} />
                            )}
                            <span style={{ overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
                              {doc.filename}
                            </span>
                          </div>
                        );
                      })
                    )}
                  </div>
                </div>
              )}
            </div>

            {/* Badges for selected documents */}
            {selectedDocs.map((doc) => (
              <span key={doc.id} className="scoped-doc-chip">
                <FileCheck size={11} />
                <span style={{ maxWidth: "140px", overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
                  {doc.filename}
                </span>
                <button onClick={() => onToggleDoc(doc.id)} className="btn-chip-remove">
                  &times;
                </button>
              </span>
            ))}
          </div>

          {/* Right Toggles */}
          <div className="toolbar-right">
            <button
              onClick={() => setShowSettings(!showSettings)}
              className={`btn-options-toggle ${showSettings ? "active" : ""}`}
              title="Retrieval algorithms & settings"
            >
              <SlidersHorizontal size={13} />
              <span>Options</span>
            </button>

            {messages.length > 0 && (
              <button
                onClick={onClear}
                className="btn-icon-subtle"
                style={{ padding: "6px 8px" }}
                title="Clear current view"
              >
                <Trash2 size={13} />
              </button>
            )}
          </div>
        </div>

        {/* Advanced Settings Drawer */}
        {showSettings && (
          <div className="options-drawer">
            <div className="options-group">
              <span style={{ fontWeight: 600, color: "var(--slate-700)" }}>Top-K: {topK}</span>
              <input
                type="range"
                min={1}
                max={10}
                value={topK}
                onChange={(e) => onTopKChange(Number(e.target.value))}
                style={{ width: "90px", cursor: "pointer", accentColor: "var(--primary)" }}
              />
            </div>

            <div className="options-group">
              <label className="option-checkbox-label">
                <input
                  type="checkbox"
                  checked={enableHybrid}
                  onChange={(e) => onToggleHybrid(e.target.checked)}
                />
                <span>Hybrid (Dense + BM25)</span>
              </label>

              <label className="option-checkbox-label">
                <input
                  type="checkbox"
                  checked={enableMmr}
                  onChange={(e) => onToggleMmr(e.target.checked)}
                />
                <span>MMR Diversity</span>
              </label>

              <label className="option-checkbox-label">
                <input
                  type="checkbox"
                  checked={enableReranking}
                  onChange={(e) => onToggleReranking(e.target.checked)}
                />
                <span>Cross-Encoder Rerank</span>
              </label>
            </div>
          </div>
        )}

        {/* Message Thread Area */}
        <div className="chat-thread-container">
          {messages.length === 0 && !streamingDelta ? (
            <div className="chat-empty-state">
              <div className="chat-empty-icon" style={{ marginBottom: "16px" }}>
                <Sparkles size={26} color="var(--primary)" />
              </div>
              <h3 style={{ fontSize: "16px", fontWeight: 700, color: "var(--slate-800)", marginBottom: "4px" }}>
                Grounded Document Q&amp;A
              </h3>
              <p style={{ fontSize: "12px", color: "var(--slate-500)", maxWidth: "420px", textAlign: "center", marginBottom: "24px" }}>
                Ask questions across all or selected documents. Answers are streamed live with real-time citations and source verification.
              </p>

              <div className="sample-questions-grid">
                {SAMPLE_QUESTIONS.map((q, idx) => (
                  <button
                    key={idx}
                    onClick={() => onAsk(q)}
                    className="sample-q-btn"
                  >
                    &ldquo;{q}&rdquo;
                  </button>
                ))}
              </div>
            </div>
          ) : (
            <>
              {messages.map((msg) => (
                <div
                  key={msg.id}
                  className={`message-item ${msg.sender === "user" ? "user" : "assistant"}`}
                >
                  <div className={`msg-avatar ${msg.sender === "user" ? "user" : "assistant"}`}>
                    {msg.sender === "user" ? <User size={15} /> : <Bot size={15} />}
                  </div>

                  <div className="msg-body-wrapper">
                    <div className="msg-bubble">
                      <p style={{ whiteSpace: "pre-wrap" }}>{msg.text}</p>
                    </div>

                    {/* Insufficient Evidence Warning Banner */}
                    {msg.isInsufficientEvidence() && (
                      <div className="insufficient-evidence-alert">
                        <AlertTriangle size={15} color="var(--amber-700)" style={{ flexShrink: 0 }} />
                        <span style={{ fontSize: "12px", color: "var(--amber-700)" }}>
                          Insufficient Evidence: The scoped documents do not contain high-confidence data for this query.
                        </span>
                      </div>
                    )}

                    {/* Prominent Evidence Filenames Used */}
                    {msg.sender === "assistant" && msg.citations && msg.citations.length > 0 && (
                      <div style={{ marginTop: "4px" }}>
                        <div style={{ display: "flex", alignItems: "center", gap: "6px", fontSize: "11px", fontWeight: 600, color: "var(--slate-500)", marginBottom: "4px" }}>
                          <Layers size={12} color="var(--primary)" />
                          <span>Evidence Sources Used ({msg.citations.length}):</span>
                        </div>
                        <div className="evidence-source-tags">
                          {Array.from(new Set(msg.citations.map((c) => c.filename))).map((fname) => (
                            <span key={fname} className="evidence-tag">
                              <FileText size={11} color="var(--primary)" />
                              <span>{fname}</span>
                            </span>
                          ))}
                        </div>
                      </div>
                    )}

                    {/* Detailed Citations Cards */}
                    {msg.hasCitations() && (
                      <div style={{ marginTop: "6px" }}>
                        <div style={{ display: "flex", alignItems: "center", gap: "4px", fontSize: "11px", fontWeight: 500, color: "var(--slate-500)", marginBottom: "4px" }}>
                          <BookMarked size={12} color="var(--primary)" />
                          <span>Detailed Chunk Snippets:</span>
                        </div>
                        <div style={{ display: "flex", flexDirection: "column", gap: "6px" }}>
                          {msg.citations.map((c, idx) => (
                            <CitationCard key={c.chunkId} citation={c} index={idx} />
                          ))}
                        </div>
                      </div>
                    )}
                  </div>
                </div>
              ))}

              {/* Real-time Streaming Response Bubble */}
              {isAsking && streamingDelta && (
                <div className="message-item assistant">
                  <div className="msg-avatar assistant">
                    <Bot size={15} />
                  </div>
                  <div className="msg-body-wrapper" style={{ maxWidth: "80%" }}>
                    <div className="msg-bubble">
                      <p style={{ whiteSpace: "pre-wrap" }}>{streamingDelta}</p>
                      <span style={{ display: "inline-block", width: "6px", height: "12px", background: "var(--primary)", marginLeft: "4px" }} />
                    </div>
                  </div>
                </div>
              )}

              {/* Loading Indicator before stream starts */}
              {isAsking && !streamingDelta && (
                <div style={{ display: "flex", alignItems: "center", gap: "8px", fontSize: "12px", color: "var(--slate-500)", padding: "4px 8px" }}>
                  <Loader2 size={15} className="spin-icon" color="var(--primary)" />
                  <span>Searching documents &amp; initializing model response...</span>
                </div>
              )}

              <div ref={messagesEndRef} />
            </>
          )}
        </div>

        {/* Input Box */}
        <div className="chat-input-bar">
          <form onSubmit={handleSubmit} className="chat-input-box">
            <textarea
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder={
                selectedDocIds.length === 1
                  ? `Ask question about selected document... (Press Enter)`
                  : selectedDocIds.length > 1
                  ? `Ask question scoped to ${selectedDocIds.length} documents... (Press Enter)`
                  : "Ask questions across all indexed documents... (Press Enter)"
              }
              rows={1}
              className="chat-input-textarea"
              disabled={isAsking}
            />
            <button
              type="submit"
              disabled={!input.trim() || isAsking}
              className="btn-chat-send"
              title="Send question"
            >
              {isAsking ? <Loader2 size={14} className="spin-icon" /> : <Send size={14} />}
            </button>
          </form>
          <div className="chat-input-footer-info">
            <span>Press <strong>Enter</strong> to send &bull; <strong>Shift + Enter</strong> for newline</span>
            <span>Real-time SSE token streaming enabled</span>
          </div>
        </div>
      </div>
    </div>
  );
};
