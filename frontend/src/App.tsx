import React, { useState } from "react";
import { Navbar } from "./components/Navbar";
import { FileUploader } from "./components/FileUploader";
import { DocumentList } from "./components/DocumentList";
import { DocumentDetailModal } from "./components/DocumentDetailModal";
import { ChatInterface } from "./components/ChatInterface";
import { useSystemHealth } from "./hooks/useSystemHealth";
import { useDocuments } from "./hooks/useDocuments";
import { useQuestionAnswering } from "./hooks/useQuestionAnswering";

export const App: React.FC = () => {
  const { health, loading: healthLoading, refreshHealth } = useSystemHealth();
  const {
    documents,
    loading: docsLoading,
    uploading,
    error: docsError,
    uploadDocument,
    deleteDocument,
    inspectDocument,
    inspectingDoc,
    inspectLoading,
    closeInspectModal,
  } = useDocuments();

  const {
    messages,
    isAsking,
    error: qaError,
    selectedDocumentId,
    setSelectedDocumentId,
    topK,
    setTopK,
    askQuestion,
    clearChat,
  } = useQuestionAnswering();

  const [activeTab, setActiveTab] = useState<"documents" | "chat">("chat");

  return (
    <div className="app-layout">
      <Navbar health={health} loading={healthLoading} onRefreshHealth={refreshHealth} />

      {/* Global alert banner if any error */}
      {(docsError || qaError) && (
        <div className="global-error-banner">
          <span>{docsError || qaError}</span>
        </div>
      )}

      {/* Mobile Tab Switcher */}
      <div className="mobile-tab-bar md:hidden">
        <button
          className={`tab-btn ${activeTab === "chat" ? "active" : ""}`}
          onClick={() => setActiveTab("chat")}
        >
          Q&amp;A Chat
        </button>
        <button
          className={`tab-btn ${activeTab === "documents" ? "active" : ""}`}
          onClick={() => setActiveTab("documents")}
        >
          Documents ({documents.length})
        </button>
      </div>

      <main className="main-content-grid">
        {/* Left Column: Document Ingestion & Management */}
        <aside className={`sidebar-column ${activeTab === "documents" ? "mobile-visible" : "mobile-hidden"}`}>
          <div className="sidebar-section-header">
            <h2 className="section-title">Document Management</h2>
            <p className="section-subtitle">Upload &amp; index PDFs, Markdown, and TXT into ChromaDB</p>
          </div>

          <FileUploader onUpload={uploadDocument} uploading={uploading} />

          <DocumentList
            documents={documents}
            loading={docsLoading}
            selectedDocId={selectedDocumentId}
            onSelectDoc={(id) => {
              setSelectedDocumentId(id);
              setActiveTab("chat"); // Switch to chat tab on mobile when document selected
            }}
            onInspectDoc={inspectDocument}
            onDeleteDoc={deleteDocument}
          />
        </aside>

        {/* Right Column: Q&A Chat & Citation Explorer */}
        <section className={`chat-column ${activeTab === "chat" ? "mobile-visible" : "mobile-hidden"}`}>
          <ChatInterface
            messages={messages}
            isAsking={isAsking}
            documents={documents}
            selectedDocId={selectedDocumentId}
            onSelectDoc={setSelectedDocumentId}
            topK={topK}
            onTopKChange={setTopK}
            onAsk={askQuestion}
            onClear={clearChat}
          />
        </section>
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
