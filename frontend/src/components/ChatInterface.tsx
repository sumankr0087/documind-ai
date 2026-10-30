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
    <div className="flex h-[720px] bg-white rounded-xl shadow-sm border border-slate-200 overflow-hidden">
      {/* 1. Topics Sidebar */}
      <div
        className={`${
          sidebarOpen ? "w-64" : "w-12"
        } transition-all duration-200 bg-slate-900 text-slate-100 flex flex-col border-r border-slate-800 shrink-0`}
      >
        <div className="p-3 border-b border-slate-800 flex items-center justify-between">
          {sidebarOpen ? (
            <>
              <button
                onClick={onCreateSession}
                className="flex items-center gap-1.5 text-xs font-semibold bg-indigo-600 hover:bg-indigo-700 text-white px-2.5 py-1.5 rounded-lg transition"
              >
                <PlusCircle size={14} /> New Topic
              </button>
              <button
                onClick={() => setSidebarOpen(false)}
                className="text-slate-400 hover:text-white text-xs p-1"
                title="Collapse Topics Sidebar"
              >
                &larr;
              </button>
            </>
          ) : (
            <button
              onClick={() => setSidebarOpen(true)}
              className="text-slate-400 hover:text-white mx-auto p-1"
              title="Expand Topics Sidebar"
            >
              <MessageSquare size={16} />
            </button>
          )}
        </div>

        {sidebarOpen && (
          <div className="flex-1 overflow-y-auto p-2 space-y-1">
            <div className="text-[10px] font-semibold tracking-wider uppercase text-slate-400 px-2 py-1">
              Chat Topics ({sessions.length})
            </div>
            {sessions.length === 0 ? (
              <div className="text-xs text-slate-500 px-2 py-3 text-center">
                No saved topics yet. Start chatting to save your conversation in SQLite.
              </div>
            ) : (
              sessions.map((s) => (
                <div
                  key={s.sessionId}
                  onClick={() => onSelectSession(s.sessionId)}
                  className={`group flex items-center justify-between text-xs px-2.5 py-2 rounded-lg cursor-pointer transition ${
                    activeSessionId === s.sessionId
                      ? "bg-indigo-600 text-white font-medium"
                      : "text-slate-300 hover:bg-slate-800 hover:text-white"
                  }`}
                >
                  <div className="flex items-center gap-2 truncate flex-1 mr-1">
                    <MessageSquare size={13} className="shrink-0" />
                    <span className="truncate">{s.title}</span>
                  </div>
                  <div className="flex items-center gap-1">
                    <span className="text-[10px] opacity-60">{s.messageCount}</span>
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        onDeleteSession(s.sessionId);
                      }}
                      className="opacity-0 group-hover:opacity-100 p-0.5 hover:text-red-400 transition"
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
      </div>

      {/* 2. Main Chat Conversation Area */}
      <div className="flex-1 flex flex-col min-w-0 bg-slate-50/50">
        {/* Top Control Bar: Document Selection & Retrieval Toggles */}
        <div className="bg-white px-4 py-2.5 border-b border-slate-200 flex items-center justify-between gap-3 flex-wrap">
          <div className="flex items-center gap-2 flex-wrap flex-1">
            {/* Multi-document scope button */}
            <div className="relative">
              <button
                onClick={() => setShowDocSelector(!showDocSelector)}
                className={`flex items-center gap-1.5 px-2.5 py-1.5 rounded-lg border text-xs font-medium transition ${
                  selectedDocIds.length > 0
                    ? "bg-indigo-50 border-indigo-200 text-indigo-700"
                    : "bg-white border-slate-200 text-slate-700 hover:bg-slate-50"
                }`}
              >
                <Filter size={13} />
                <span>
                  {selectedDocIds.length === 0
                    ? `Searching All Documents (${documents.length})`
                    : `Scoped to ${selectedDocIds.length} Selected Document(s)`}
                </span>
              </button>

              {/* Document selection dropdown */}
              {showDocSelector && (
                <div className="absolute left-0 mt-1.5 w-72 bg-white rounded-xl shadow-lg border border-slate-200 p-2 z-30">
                  <div className="flex items-center justify-between pb-1.5 mb-1.5 border-b border-slate-100">
                    <span className="text-xs font-semibold text-slate-700">Select Scope:</span>
                    {selectedDocIds.length > 0 && (
                      <button
                        onClick={onClearDocSelection}
                        className="text-[11px] text-indigo-600 hover:underline"
                      >
                        Reset to All
                      </button>
                    )}
                  </div>
                  <div className="max-h-56 overflow-y-auto space-y-1">
                    {documents.length === 0 ? (
                      <p className="text-xs text-slate-400 p-2 text-center">No documents uploaded yet.</p>
                    ) : (
                      documents.map((doc) => {
                        const isChecked = selectedDocIds.includes(doc.id);
                        return (
                          <div
                            key={doc.id}
                            onClick={() => onToggleDoc(doc.id)}
                            className="flex items-center gap-2 p-1.5 hover:bg-slate-50 rounded cursor-pointer text-xs text-slate-700"
                          >
                            {isChecked ? (
                              <CheckSquare size={14} className="text-indigo-600 shrink-0" />
                            ) : (
                              <Square size={14} className="text-slate-300 shrink-0" />
                            )}
                            <span className="truncate">{doc.filename}</span>
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
              <span
                key={doc.id}
                className="inline-flex items-center gap-1 bg-indigo-100/70 text-indigo-800 text-[11px] px-2 py-0.5 rounded-full"
              >
                <FileCheck size={11} />
                <span className="truncate max-w-[140px]">{doc.filename}</span>
                <button onClick={() => onToggleDoc(doc.id)} className="hover:text-indigo-950 font-bold ml-0.5">
                  &times;
                </button>
              </span>
            ))}
          </div>

          {/* Right Toggles */}
          <div className="flex items-center gap-2">
            <button
              onClick={() => setShowSettings(!showSettings)}
              className={`flex items-center gap-1 px-2 py-1 rounded text-xs border transition ${
                showSettings
                  ? "bg-indigo-50 border-indigo-200 text-indigo-600"
                  : "bg-white border-slate-200 text-slate-600 hover:bg-slate-50"
              }`}
              title="Retrieval algorithms & settings"
            >
              <SlidersHorizontal size={13} />
              <span>Options</span>
            </button>

            {messages.length > 0 && (
              <button
                onClick={onClear}
                className="p-1.5 text-slate-400 hover:text-red-500 rounded transition"
                title="Clear current view"
              >
                <Trash2 size={14} />
              </button>
            )}
          </div>
        </div>

        {/* Advanced Settings Drawer */}
        {showSettings && (
          <div className="bg-slate-100/80 px-4 py-2 border-b border-slate-200 flex items-center justify-between gap-4 text-xs flex-wrap">
            <div className="flex items-center gap-2">
              <span className="text-slate-600 font-medium">Top-K: {topK}</span>
              <input
                type="range"
                min={1}
                max={10}
                value={topK}
                onChange={(e) => onTopKChange(Number(e.target.value))}
                className="w-24 accent-indigo-600 cursor-pointer"
              />
            </div>

            <div className="flex items-center gap-4">
              <label className="flex items-center gap-1.5 cursor-pointer">
                <input
                  type="checkbox"
                  checked={enableHybrid}
                  onChange={(e) => onToggleHybrid(e.target.checked)}
                  className="rounded text-indigo-600"
                />
                <span className="font-medium text-slate-700">Hybrid (Dense + BM25)</span>
              </label>

              <label className="flex items-center gap-1.5 cursor-pointer">
                <input
                  type="checkbox"
                  checked={enableMmr}
                  onChange={(e) => onToggleMmr(e.target.checked)}
                  className="rounded text-indigo-600"
                />
                <span className="font-medium text-slate-700">MMR Diversity</span>
              </label>

              <label className="flex items-center gap-1.5 cursor-pointer">
                <input
                  type="checkbox"
                  checked={enableReranking}
                  onChange={(e) => onToggleReranking(e.target.checked)}
                  className="rounded text-indigo-600"
                />
                <span className="font-medium text-slate-700">Cross-Encoder Rerank</span>
              </label>
            </div>
          </div>
        )}

        {/* Message Thread Area */}
        <div className="flex-1 overflow-y-auto p-4 space-y-4">
          {messages.length === 0 && !streamingDelta ? (
            <div className="flex flex-col items-center justify-center h-full text-center p-6">
              <div className="w-12 h-12 rounded-full bg-indigo-50 flex items-center justify-center text-indigo-600 mb-3 shadow-inner">
                <Sparkles size={24} />
              </div>
              <h3 className="font-bold text-slate-800 text-sm">Grounded Document Q&amp;A</h3>
              <p className="text-xs text-slate-500 max-w-sm mt-1">
                Ask questions across all or selected documents. Answers are streamed live with real-time citations and source verification.
              </p>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 max-w-lg mt-5 w-full">
                {SAMPLE_QUESTIONS.map((q, idx) => (
                  <button
                    key={idx}
                    onClick={() => onAsk(q)}
                    className="text-left text-xs p-2.5 rounded-lg border border-slate-200 bg-white hover:border-indigo-300 hover:shadow-sm text-slate-700 transition"
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
                  className={`flex gap-2.5 ${msg.sender === "user" ? "justify-end" : "justify-start"}`}
                >
                  {msg.sender === "assistant" && (
                    <div className="w-7 h-7 rounded-full bg-indigo-600 text-white flex items-center justify-center shrink-0 mt-0.5">
                      <Bot size={15} />
                    </div>
                  )}

                  <div className={`max-w-[80%] space-y-1.5 ${msg.sender === "user" ? "items-end" : "items-start"}`}>
                    <div
                      className={`px-3.5 py-2.5 rounded-2xl text-xs leading-relaxed ${
                        msg.sender === "user"
                          ? "bg-indigo-600 text-white rounded-br-none"
                          : "bg-white text-slate-800 shadow-sm border border-slate-200 rounded-bl-none"
                      }`}
                    >
                      <p className="whitespace-pre-wrap">{msg.text}</p>
                    </div>

                    {/* Insufficient Evidence Warning Banner */}
                    {msg.isInsufficientEvidence() && (
                      <div className="flex items-center gap-1.5 text-xs text-amber-800 bg-amber-50 border border-amber-200 px-3 py-1.5 rounded-lg">
                        <AlertTriangle size={14} className="text-amber-600 shrink-0" />
                        <span>Insufficient Evidence: The scoped documents do not contain high-confidence data for this query.</span>
                      </div>
                    )}

                    {/* Prominent Evidence Filenames Used */}
                    {msg.sender === "assistant" && msg.citations && msg.citations.length > 0 && (
                      <div className="pt-1">
                        <div className="flex items-center gap-1.5 text-[11px] font-semibold text-slate-500 mb-1">
                          <Layers size={12} className="text-indigo-600" />
                          <span>Evidence Sources Used ({msg.citations.length}):</span>
                        </div>
                        <div className="flex flex-wrap gap-1.5">
                          {Array.from(new Set(msg.citations.map((c) => c.filename))).map((fname) => (
                            <span
                              key={fname}
                              className="inline-flex items-center gap-1 bg-slate-100 hover:bg-slate-200 text-slate-700 border border-slate-300 text-[11px] font-medium px-2 py-0.5 rounded-md transition"
                            >
                              <FileText size={11} className="text-indigo-600" />
                              <span>{fname}</span>
                            </span>
                          ))}
                        </div>
                      </div>
                    )}

                    {/* Detailed Citations Cards */}
                    {msg.hasCitations() && (
                      <div className="pt-1">
                        <div className="flex items-center gap-1 text-[11px] font-medium text-slate-500 mb-1">
                          <BookMarked size={12} className="text-indigo-500" />
                          <span>Detailed Chunk Snippets:</span>
                        </div>
                        <div className="grid grid-cols-1 gap-1.5">
                          {msg.citations.map((c, idx) => (
                            <CitationCard key={c.chunkId} citation={c} index={idx} />
                          ))}
                        </div>
                      </div>
                    )}
                  </div>

                  {msg.sender === "user" && (
                    <div className="w-7 h-7 rounded-full bg-slate-700 text-white flex items-center justify-center shrink-0 mt-0.5">
                      <User size={15} />
                    </div>
                  )}
                </div>
              ))}

              {/* Real-time Streaming Response Bubble */}
              {isAsking && streamingDelta && (
                <div className="flex gap-2.5 justify-start">
                  <div className="w-7 h-7 rounded-full bg-indigo-600 text-white flex items-center justify-center shrink-0 mt-0.5">
                    <Bot size={15} />
                  </div>
                  <div className="max-w-[80%]">
                    <div className="px-3.5 py-2.5 rounded-2xl bg-white text-slate-800 shadow-sm border border-slate-200 rounded-bl-none text-xs leading-relaxed">
                      <p className="whitespace-pre-wrap">{streamingDelta}</p>
                      <span className="inline-block w-1.5 h-3 bg-indigo-600 ml-1 animate-pulse" />
                    </div>
                  </div>
                </div>
              )}

              {/* Loading Indicator before stream starts */}
              {isAsking && !streamingDelta && (
                <div className="flex items-center gap-2 text-slate-500 text-xs px-2 py-1">
                  <Loader2 size={14} className="spin-icon text-indigo-600" />
                  <span>Searching documents &amp; initializing model response...</span>
                </div>
              )}

              <div ref={messagesEndRef} />
            </>
          )}
        </div>

        {/* Input Box */}
        <div className="p-3 bg-white border-t border-slate-200">
          <form onSubmit={handleSubmit} className="flex items-center gap-2 bg-slate-50 border border-slate-300 rounded-xl px-3 py-2 focus-within:border-indigo-500 focus-within:ring-1 focus-within:ring-indigo-500">
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
              className="flex-1 bg-transparent resize-none outline-none text-xs text-slate-800 placeholder-slate-400"
              disabled={isAsking}
            />
            <button
              type="submit"
              disabled={!input.trim() || isAsking}
              className="p-1.5 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 disabled:opacity-40 transition"
            >
              {isAsking ? <Loader2 size={14} className="spin-icon" /> : <Send size={14} />}
            </button>
          </form>
          <div className="flex items-center justify-between text-[10px] text-slate-400 px-1 mt-1">
            <span>Press <strong>Enter</strong> to send &bull; <strong>Shift + Enter</strong> for newline</span>
            <span>Real-time SSE token streaming enabled</span>
          </div>
        </div>
      </div>
    </div>
  );
};
