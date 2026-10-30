import React, { useState, useRef, useEffect } from "react";
import { useSystemHealth } from "./hooks/useSystemHealth";
import { useDocuments } from "./hooks/useDocuments";
import { useQuestionAnswering } from "./hooks/useQuestionAnswering";
import { DocumentDetailModal } from "./components/DocumentDetailModal";
import { CitationCard } from "./components/CitationCard";
import {
  Brain,
  Plus,
  MessageSquare,
  FileText,
  UploadCloud,
  Trash2,
  Eye,
  PanelLeftClose,
  PanelLeft,
  Filter,
  SlidersHorizontal,
  Send,
  Loader2,
  Sparkles,
  Bot,
  User,
  AlertTriangle,
  Layers,
  FileCode2,
  ExternalLink,
  CheckSquare,
  Square,
} from "lucide-react";

const SAMPLE_PROMPTS = [
  {
    title: "Document Summary",
    desc: "Summarize key findings, main ideas, and architecture.",
    query: "Summarize the key findings, core architecture, and main takeaways from this document.",
  },
  {
    title: "Technical Requirements",
    desc: "Extract prerequisites, libraries, and dependencies.",
    query: "What tools, libraries, credentials, or system dependencies are mentioned in the text?",
  },
  {
    title: "Methodology & Setup",
    desc: "Explain how components connect and operate.",
    query: "Explain the implementation steps, methodology, and structural components detailed in the document.",
  },
  {
    title: "Security & Guidelines",
    desc: "Identify security policies and recommended actions.",
    query: "What security guidelines, risk mitigations, or recommended procedures are outlined?",
  },
];

export const App: React.FC = () => {
  const { health, loading: healthLoading } = useSystemHealth();
  const {
    documents,
    loading: docsLoading,
    uploading,
    uploadStatus,
    uploadBatch,
    deleteDocument,
    inspectDocument,
    inspectingDoc,
    inspectLoading,
    closeInspectModal,
  } = useDocuments();

  const {
    messages,
    isAsking,
    streamingDelta,
    selectedDocumentIds,
    toggleDocumentSelection,
    clearDocumentSelection,
    topK,
    setTopK,
    enableMmr,
    setEnableMmr,
    enableHybrid,
    setEnableHybrid,
    enableReranking,
    setEnableReranking,
    sessions,
    activeSessionId,
    setActiveSessionId,
    createNewTopic,
    deleteTopic,
    askQuestion,
    clearChat,
  } = useQuestionAnswering();

  const [sidebarOpen, setSidebarOpen] = useState(true);
  const [sidebarTab, setSidebarTab] = useState<"topics" | "docs">("topics");
  const [showScopeDropdown, setShowScopeDropdown] = useState(false);
  const [showSettingsDrawer, setShowSettingsDrawer] = useState(false);
  const [inputText, setInputText] = useState("");
  const fileInputRef = useRef<HTMLInputElement>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  // Auto-scroll chat to bottom
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, isAsking, streamingDelta]);

  // Adjust textarea height dynamically
  const handleInputChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    setInputText(e.target.value);
    if (textareaRef.current) {
      textareaRef.current.style.height = "auto";
      textareaRef.current.style.height = `${Math.min(textareaRef.current.scrollHeight, 160)}px`;
    }
  };

  const handleSendMessage = (e?: React.FormEvent) => {
    if (e) e.preventDefault();
    if (!inputText.trim() || isAsking) return;
    askQuestion(inputText);
    setInputText("");
    if (textareaRef.current) {
      textareaRef.current.style.height = "auto";
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  const handleFileDrop = (e: React.DragEvent) => {
    e.preventDefault();
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      uploadBatch(Array.from(e.dataTransfer.files));
    }
  };

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files.length > 0) {
      uploadBatch(Array.from(e.target.files));
    }
  };

  const activeTopic = sessions.find((s) => s.sessionId === activeSessionId);
  const selectedDocs = documents.filter((d) => selectedDocumentIds.includes(d.id));

  return (
    <div className="chatgpt-app">
      {/* 1. ChatGPT Left Dark Sidebar */}
      <aside className={`chatgpt-sidebar ${sidebarOpen ? "" : "collapsed"}`}>
        <div className="sidebar-header">
          <div className="sidebar-brand">
            <div className="brand-icon-box">
              <Brain size={18} />
            </div>
            <span className="brand-name">DocuMind AI</span>
          </div>
          <button
            onClick={() => setSidebarOpen(false)}
            className="sidebar-toggle-btn"
            title="Close sidebar"
          >
            <PanelLeftClose size={18} />
          </button>
        </div>

        {/* New Chat Button */}
        <div className="new-chat-wrapper">
          <button
            onClick={() => {
              createNewTopic();
              setSidebarTab("topics");
            }}
            className="btn-new-chat"
          >
            <Plus size={16} />
            <span>New chat</span>
          </button>
        </div>

        {/* Sidebar View Tabs: Topics vs Documents */}
        <div className="sidebar-tabs">
          <button
            onClick={() => setSidebarTab("topics")}
            className={`sidebar-tab-btn ${sidebarTab === "topics" ? "active" : ""}`}
          >
            <MessageSquare size={13} />
            <span>Chats ({sessions.length})</span>
          </button>
          <button
            onClick={() => setSidebarTab("docs")}
            className={`sidebar-tab-btn ${sidebarTab === "docs" ? "active" : ""}`}
          >
            <FileText size={13} />
            <span>Docs ({documents.length})</span>
          </button>
        </div>

        {/* Sidebar Scroll Area */}
        <div className="sidebar-scroll-area">
          {sidebarTab === "topics" ? (
            <>
              <div className="sidebar-section-label">Recent Conversations</div>
              {sessions.length === 0 ? (
                <div style={{ fontSize: "12px", color: "var(--sidebar-muted)", padding: "16px 8px", textAlign: "center" }}>
                  No saved conversations yet. Start chatting to save in SQLite.
                </div>
              ) : (
                sessions.map((s) => (
                  <div
                    key={s.sessionId}
                    onClick={() => setActiveSessionId(s.sessionId)}
                    className={`sidebar-topic-item ${activeSessionId === s.sessionId ? "active" : ""}`}
                  >
                    <div className="topic-text">
                      <MessageSquare size={14} style={{ flexShrink: 0, opacity: 0.7 }} />
                      <span title={s.title}>{s.title}</span>
                    </div>
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        deleteTopic(s.sessionId);
                      }}
                      className="btn-topic-delete"
                      title="Delete conversation"
                    >
                      <Trash2 size={13} />
                    </button>
                  </div>
                ))
              )}
            </>
          ) : (
            <>
              {/* Document Uploader */}
              <div
                className="doc-upload-box"
                onDragOver={(e) => e.preventDefault()}
                onDrop={handleFileDrop}
                onClick={() => fileInputRef.current?.click()}
              >
                <input
                  type="file"
                  multiple
                  ref={fileInputRef}
                  style={{ display: "none" }}
                  accept=".pdf,.txt,.md"
                  onChange={handleFileSelect}
                />
                <UploadCloud size={20} color="#818cf8" style={{ margin: "0 auto" }} />
                <p>{uploading ? "Indexing files..." : "Upload Documents"}</p>
                <span>Drop PDF, Markdown, or TXT</span>
              </div>

              {uploadStatus && (
                <div style={{ fontSize: "11px", color: "#818cf8", padding: "4px 8px", marginBottom: "8px", textAlign: "center" }}>
                  {uploadStatus}
                </div>
              )}

              <div className="sidebar-section-label">Indexed Documents ({documents.length})</div>
              {documents.length === 0 ? (
                <div style={{ fontSize: "12px", color: "var(--sidebar-muted)", padding: "12px 8px", textAlign: "center" }}>
                  {docsLoading ? "Loading documents..." : "No documents indexed yet."}
                </div>
              ) : (
                documents.map((doc) => {
                  const isScoped = selectedDocumentIds.includes(doc.id);
                  return (
                    <div
                      key={doc.id}
                      className={`sidebar-doc-card ${isScoped ? "scoped" : ""}`}
                      onClick={() => toggleDocumentSelection(doc.id)}
                      title="Click to toggle search scope"
                    >
                      <div className="doc-info-col">
                        <div className="doc-filename-row">
                          {isScoped ? (
                            <CheckSquare size={13} color="#818cf8" style={{ flexShrink: 0 }} />
                          ) : (
                            <Square size={13} color="#6b7280" style={{ flexShrink: 0 }} />
                          )}
                          <span className="doc-filename-text">{doc.filename}</span>
                        </div>
                        <span className="doc-meta-sub">
                          {doc.getFormattedSize()} &bull; {doc.chunkCount} chunks
                        </span>
                      </div>

                      <div className="doc-action-icons">
                        <button
                          onClick={(e) => {
                            e.stopPropagation();
                            inspectDocument(doc.id);
                          }}
                          className="btn-doc-icon"
                          title="Inspect chunks"
                        >
                          <Eye size={13} />
                        </button>
                        <button
                          onClick={(e) => {
                            e.stopPropagation();
                            if (window.confirm(`Delete '${doc.filename}' from ChromaDB?`)) {
                              deleteDocument(doc.id);
                            }
                          }}
                          className="btn-doc-icon danger"
                          title="Delete document"
                        >
                          <Trash2 size={13} />
                        </button>
                      </div>
                    </div>
                  );
                })
              )}
            </>
          )}
        </div>

        {/* Sidebar Footer */}
        <div className="sidebar-footer">
          <div className="health-status-row">
            <span>DocuMind Engine</span>
            <span className="status-pill-indicator">
              <span style={{ width: 6, height: 6, borderRadius: "50%", backgroundColor: "#10b981", display: "inline-block" }} />
              {healthLoading ? "Checking..." : health?.status === "healthy" ? "Online" : "Ready"}
            </span>
          </div>

          <div className="footer-nav-links">
            <a href="/docs" target="_blank" rel="noopener noreferrer">
              <FileCode2 size={12} />
              <span>API Docs</span>
              <ExternalLink size={10} style={{ opacity: 0.6 }} />
            </a>
            <a href="https://github.com/sumankr0087/documind-ai" target="_blank" rel="noopener noreferrer">
              <span>GitHub</span>
              <ExternalLink size={10} style={{ opacity: 0.6 }} />
            </a>
          </div>
        </div>
      </aside>

      {/* 2. Main Chat View */}
      <main className="chatgpt-main">
        {/* Top Minimal Header */}
        <header className="chatgpt-top-header">
          <div className="top-left-actions">
            {!sidebarOpen && (
              <button
                onClick={() => setSidebarOpen(true)}
                className="btn-collapse-toggle"
                title="Open sidebar"
              >
                <PanelLeft size={18} />
              </button>
            )}
            <h2 className="chat-topic-header-title">
              {activeTopic ? activeTopic.title : "Document Q&A"}
            </h2>
          </div>

          <div className="top-right-actions">
            {/* Search Scope Pill Button */}
            <div style={{ position: "relative" }}>
              <button
                onClick={() => setShowScopeDropdown(!showScopeDropdown)}
                className={`btn-scope-pill ${selectedDocumentIds.length > 0 ? "active" : ""}`}
              >
                <Filter size={13} />
                <span>
                  {selectedDocumentIds.length === 0
                    ? `All Documents (${documents.length})`
                    : selectedDocumentIds.length === 1
                    ? selectedDocs[0]?.filename || "1 Document"
                    : `${selectedDocumentIds.length} Documents Selected`}
                </span>
              </button>

              {/* Scope Dropdown */}
              {showScopeDropdown && (
                <div className="scope-dropdown-container">
                  <div className="scope-dropdown-title-row">
                    <span>Search Scope Filter</span>
                    {selectedDocumentIds.length > 0 && (
                      <button
                        onClick={() => clearDocumentSelection()}
                        style={{ background: "transparent", border: "none", color: "var(--primary)", fontSize: "11px", fontWeight: 600, cursor: "pointer" }}
                      >
                        Reset to All
                      </button>
                    )}
                  </div>
                  <div className="scope-docs-scroll">
                    {documents.length === 0 ? (
                      <p style={{ fontSize: "12px", color: "var(--text-muted)", padding: "10px", textAlign: "center" }}>
                        No documents uploaded yet.
                      </p>
                    ) : (
                      documents.map((doc) => {
                        const isChecked = selectedDocumentIds.includes(doc.id);
                        return (
                          <div
                            key={doc.id}
                            className="scope-row-item"
                            onClick={() => toggleDocumentSelection(doc.id)}
                          >
                            {isChecked ? (
                              <CheckSquare size={14} color="var(--primary)" style={{ flexShrink: 0 }} />
                            ) : (
                              <Square size={14} color="var(--text-light)" style={{ flexShrink: 0 }} />
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

            {/* Settings Pill */}
            <div style={{ position: "relative" }}>
              <button
                onClick={() => setShowSettingsDrawer(!showSettingsDrawer)}
                className={`btn-settings-pill ${showSettingsDrawer ? "active" : ""}`}
                title="Retrieval algorithm settings"
              >
                <SlidersHorizontal size={13} />
                <span>Options</span>
              </button>

              {/* Retrieval Options Dropdown Drawer */}
              {showSettingsDrawer && (
                <div className="retrieval-drawer-dropdown">
                  <div className="drawer-row">
                    <span style={{ fontWeight: 600 }}>Top-K Chunks: {topK}</span>
                    <input
                      type="range"
                      min={1}
                      max={10}
                      value={topK}
                      onChange={(e) => setTopK(Number(e.target.value))}
                      style={{ width: "90px", accentColor: "var(--primary)", cursor: "pointer" }}
                    />
                  </div>

                  <label className="drawer-checkbox-label">
                    <input
                      type="checkbox"
                      checked={enableHybrid}
                      onChange={(e) => setEnableHybrid(e.target.checked)}
                    />
                    <span>BM25 Hybrid Search</span>
                  </label>

                  <label className="drawer-checkbox-label">
                    <input
                      type="checkbox"
                      checked={enableMmr}
                      onChange={(e) => setEnableMmr(e.target.checked)}
                    />
                    <span>MMR Diversity ($\lambda=0.7$)</span>
                  </label>

                  <label className="drawer-checkbox-label">
                    <input
                      type="checkbox"
                      checked={enableReranking}
                      onChange={(e) => setEnableReranking(e.target.checked)}
                    />
                    <span>Cross-Encoder Reranker</span>
                  </label>
                </div>
              )}
            </div>

            {/* Clear Chat Button */}
            {messages.length > 0 && (
              <button
                onClick={clearChat}
                className="btn-collapse-toggle"
                title="Clear conversation"
              >
                <Trash2 size={16} />
              </button>
            )}
          </div>
        </header>

        {/* Chat Scroll Viewport */}
        <div className="chat-viewport">
          <div className="chat-conversation-container">
            {messages.length === 0 && !streamingDelta ? (
              /* ChatGPT Empty State */
              <div className="chat-welcome-state">
                <div className="welcome-avatar-circle">
                  <Sparkles size={28} />
                </div>
                <h1 className="welcome-title">What would you like to explore?</h1>
                <p className="welcome-subtitle">
                  Ask questions across all indexed documents. Answers are generated with verifiable citations and source snippets.
                </p>

                <div className="prompt-suggestions-grid">
                  {SAMPLE_PROMPTS.map((item, idx) => (
                    <button
                      key={idx}
                      onClick={() => askQuestion(item.query)}
                      className="prompt-card-btn"
                    >
                      <span className="prompt-card-title">{item.title}</span>
                      <span className="prompt-card-desc">{item.desc}</span>
                    </button>
                  ))}
                </div>
              </div>
            ) : (
              /* Active Messages */
              messages.map((msg) => (
                <div
                  key={msg.id}
                  className={`message-turn ${msg.sender === "user" ? "user" : "assistant"}`}
                >
                  <div className={`turn-avatar ${msg.sender === "user" ? "user" : "assistant"}`}>
                    {msg.sender === "user" ? <User size={16} /> : <Bot size={16} />}
                  </div>

                  <div className="turn-content">
                    <div className="turn-bubble">
                      <p style={{ whiteSpace: "pre-wrap" }}>{msg.text}</p>
                    </div>

                    {/* Insufficient Evidence Warning Banner */}
                    {msg.isInsufficientEvidence() && (
                      <div style={{ display: "flex", alignItems: "center", gap: "8px", background: "#fffbeb", border: "1px solid #fef3c7", padding: "8px 12px", borderRadius: "8px", color: "#b45309", fontSize: "12px" }}>
                        <AlertTriangle size={15} style={{ flexShrink: 0 }} />
                        <span>Insufficient Evidence: The selected documents do not contain direct answers to this question.</span>
                      </div>
                    )}

                    {/* Evidence Sources Badge */}
                    {msg.sender === "assistant" && msg.citations && msg.citations.length > 0 && (
                      <div className="evidence-container">
                        <div className="evidence-label">
                          <Layers size={13} color="var(--primary)" />
                          <span>Sources Referenced ({msg.citations.length}):</span>
                        </div>
                        <div className="evidence-tags-row">
                          {Array.from(new Set(msg.citations.map((c) => c.filename))).map((fname) => (
                            <span key={fname} className="evidence-pill">
                              <FileText size={11} color="var(--primary)" />
                              <span>{fname}</span>
                            </span>
                          ))}
                        </div>

                        {/* Collapsible Citation Cards */}
                        <div style={{ display: "flex", flexDirection: "column", gap: "6px", marginTop: "4px" }}>
                          {msg.citations.map((c, idx) => (
                            <CitationCard key={c.chunkId} citation={c} index={idx} />
                          ))}
                        </div>
                      </div>
                    )}
                  </div>
                </div>
              ))
            )}

            {/* Real-time Streaming Bubble */}
            {isAsking && streamingDelta && (
              <div className="message-turn assistant">
                <div className="turn-avatar assistant">
                  <Bot size={16} />
                </div>
                <div className="turn-content">
                  <div className="turn-bubble">
                    <p style={{ whiteSpace: "pre-wrap" }}>{streamingDelta}</p>
                    <span className="streaming-cursor" />
                  </div>
                </div>
              </div>
            )}

            {/* Loading Indicator before first token */}
            {isAsking && !streamingDelta && (
              <div style={{ display: "flex", alignItems: "center", gap: "8px", fontSize: "13px", color: "var(--text-muted)", padding: "12px 0" }}>
                <Loader2 size={16} className="spin-icon" color="var(--primary)" />
                <span>Searching ChromaDB &amp; generating response...</span>
              </div>
            )}

            <div ref={messagesEndRef} />
          </div>
        </div>

        {/* 3. Floating Bottom ChatGPT Input Box */}
        <div className="chatgpt-bottom-anchor">
          <div className="chatgpt-input-pill-wrapper">
            <form onSubmit={handleSendMessage} className="chatgpt-input-box">
              <textarea
                ref={textareaRef}
                value={inputText}
                onChange={handleInputChange}
                onKeyDown={handleKeyDown}
                placeholder={
                  selectedDocumentIds.length === 1
                    ? `Ask about ${selectedDocs[0]?.filename || "document"}...`
                    : selectedDocumentIds.length > 1
                    ? `Ask across ${selectedDocumentIds.length} selected documents...`
                    : "Ask anything about your documents..."
                }
                rows={1}
                className="chatgpt-textarea"
                disabled={isAsking}
              />
              <button
                type="submit"
                disabled={!inputText.trim() || isAsking}
                className="btn-chatgpt-send"
                title="Send question"
              >
                {isAsking ? <Loader2 size={15} className="spin-icon" /> : <Send size={15} />}
              </button>
            </form>
            <p className="input-disclaimer-text">
              DocuMind AI provides grounded retrieval. Verify citations for critical details.
            </p>
          </div>
        </div>
      </main>

      {/* Document Chunks Inspector Modal */}
      <DocumentDetailModal
        data={inspectingDoc}
        loading={inspectLoading}
        onClose={closeInspectModal}
      />
    </div>
  );
};

export default App;
