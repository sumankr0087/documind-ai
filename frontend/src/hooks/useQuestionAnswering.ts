import { useState, useCallback, useEffect } from "react";
import { QAMessageModel, ChatSessionModel } from "../models";
import { ServiceFactory, ApiException } from "../services";

export function useQuestionAnswering() {
  const [messages, setMessages] = useState<QAMessageModel[]>([]);
  const [isAsking, setIsAsking] = useState<boolean>(false);
  const [streamingDelta, setStreamingDelta] = useState<string>("");
  const [error, setError] = useState<string | null>(null);

  // Multi-document selection
  const [selectedDocumentIds, setSelectedDocumentIds] = useState<string[]>([]);
  const [topK, setTopK] = useState<number>(5);

  // Advanced retrieval options
  const [enableMmr, setEnableMmr] = useState<boolean>(true);
  const [enableHybrid, setEnableHybrid] = useState<boolean>(true);
  const [enableReranking, setEnableReranking] = useState<boolean>(false);

  // Chat sessions / topics
  const [sessions, setSessions] = useState<ChatSessionModel[]>([]);
  const [activeSessionId, setActiveSessionId] = useState<string | null>(null);
  const [sessionsLoading, setSessionsLoading] = useState<boolean>(false);

  const fetchSessions = useCallback(async () => {
    try {
      setSessionsLoading(true);
      const chatService = ServiceFactory.getInstance().getChatService();
      const list = await chatService.listSessions();
      setSessions(list);
      // Select first session if none selected
      if (!activeSessionId && list.length > 0) {
        setActiveSessionId(list[0].sessionId);
      }
    } catch (err) {
      console.warn("Failed to load chat topics:", err);
    } finally {
      setSessionsLoading(false);
    }
  }, [activeSessionId]);

  useEffect(() => {
    fetchSessions();
  }, [fetchSessions]);

  // Load session messages when activeSessionId changes
  useEffect(() => {
    if (!activeSessionId) {
      setMessages([]);
      return;
    }
    const loadSession = async () => {
      try {
        const chatService = ServiceFactory.getInstance().getChatService();
        const data = await chatService.getSession(activeSessionId);
        const converted = data.messages.map((m) =>
          m.isUser
            ? QAMessageModel.createUserMessage(m.content)
            : QAMessageModel.createAssistantMessage({
                question: "",
                answer: m.content,
                citations: m.citations.map((c) => ({
                  chunk_id: c.chunkId,
                  document_id: c.documentId,
                  filename: c.filename,
                  page_number: c.pageNumber,
                  snippet: c.snippet,
                  relevance_score: c.relevanceScore,
                })),
                evidence_sufficient: true,
                document_id: null,
                model_used: "DocuMind-Engine",
              })
        );
        setMessages(converted);
      } catch (err) {
        console.warn("Failed to load session messages:", err);
      }
    };
    loadSession();
  }, [activeSessionId]);

  const createNewTopic = async (title?: string) => {
    try {
      const chatService = ServiceFactory.getInstance().getChatService();
      const newSession = await chatService.createSession(title || "New Topic");
      setSessions((prev) => [newSession, ...prev]);
      setActiveSessionId(newSession.sessionId);
      setMessages([]);
      return newSession;
    } catch (err) {
      console.error("Failed to create new topic:", err);
      return null;
    }
  };

  const deleteTopic = async (sessionId: string) => {
    try {
      const chatService = ServiceFactory.getInstance().getChatService();
      await chatService.deleteSession(sessionId);
      setSessions((prev) => prev.filter((s) => s.sessionId !== sessionId));
      if (activeSessionId === sessionId) {
        setActiveSessionId(null);
        setMessages([]);
      }
    } catch (err) {
      console.error("Failed to delete topic:", err);
    }
  };

  const askQuestion = useCallback(
    async (questionText: string) => {
      const trimmed = questionText.trim();
      if (!trimmed || isAsking) return;

      // Auto-create a session if none active
      let currentSessionId = activeSessionId;
      if (!currentSessionId) {
        const chatService = ServiceFactory.getInstance().getChatService();
        const newSession = await chatService.createSession(trimmed.slice(0, 30) || "New Chat");
        currentSessionId = newSession.sessionId;
        setActiveSessionId(currentSessionId);
        setSessions((prev) => [newSession, ...prev]);
      }

      const userMsg = QAMessageModel.createUserMessage(trimmed, selectedDocumentIds[0] || null);
      setMessages((prev) => [...prev, userMsg]);
      setIsAsking(true);
      setStreamingDelta("");
      setError(null);

      const questionService = ServiceFactory.getInstance().getQuestionService();

      await questionService.askQuestionStream(
        {
          question: trimmed,
          documentIds: selectedDocumentIds.length > 0 ? selectedDocumentIds : null,
          sessionId: currentSessionId,
          topK,
          enableMmr,
          enableHybrid,
          enableReranking,
        },
        (delta: string) => {
          setStreamingDelta((prev) => prev + delta);
        },
        (assistantMsg: QAMessageModel) => {
          setMessages((prev) => [...prev, assistantMsg]);
          setStreamingDelta("");
          setIsAsking(false);
          // Refresh session list to update message counts & timestamps
          fetchSessions();
        },
        (err: Error) => {
          const errorText =
            err instanceof ApiException ? err.getDisplayMessage() : err.message || "Streaming failed.";
          setError(errorText);
          setMessages((prev) => [...prev, QAMessageModel.createErrorMessage(errorText)]);
          setStreamingDelta("");
          setIsAsking(false);
        }
      );
    },
    [
      isAsking,
      activeSessionId,
      selectedDocumentIds,
      topK,
      enableMmr,
      enableHybrid,
      enableReranking,
      fetchSessions,
    ]
  );

  const toggleDocumentSelection = (docId: string) => {
    setSelectedDocumentIds((prev) =>
      prev.includes(docId) ? prev.filter((id) => id !== docId) : [...prev, docId]
    );
  };

  const clearDocumentSelection = () => {
    setSelectedDocumentIds([]);
  };

  const clearChat = useCallback(() => {
    setMessages([]);
    setError(null);
    setStreamingDelta("");
  }, []);

  return {
    messages,
    isAsking,
    streamingDelta,
    error,
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
    sessionsLoading,
    createNewTopic,
    deleteTopic,
    askQuestion,
    clearChat,
  };
}
