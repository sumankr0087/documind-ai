import { useState, useCallback } from "react";
import { QAMessageModel } from "../models";
import { ServiceFactory, ApiException } from "../services";

export function useQuestionAnswering() {
  const [messages, setMessages] = useState<QAMessageModel[]>([]);
  const [isAsking, setIsAsking] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [selectedDocumentId, setSelectedDocumentId] = useState<string | null>(null);
  const [topK, setTopK] = useState<number>(5);

  const askQuestion = useCallback(
    async (questionText: string) => {
      const trimmed = questionText.trim();
      if (!trimmed || isAsking) return;

      const userMsg = QAMessageModel.createUserMessage(trimmed, selectedDocumentId);
      setMessages((prev) => [...prev, userMsg]);
      setIsAsking(true);
      setError(null);

      try {
        const questionService = ServiceFactory.getInstance().getQuestionService();
        const assistantMsg = await questionService.askQuestion(trimmed, selectedDocumentId, topK);
        setMessages((prev) => [...prev, assistantMsg]);
      } catch (err: unknown) {
        const errorText =
          err instanceof ApiException ? err.getDisplayMessage() : "Failed to obtain answer from backend.";
        setError(errorText);
        setMessages((prev) => [...prev, QAMessageModel.createErrorMessage(errorText)]);
      } finally {
        setIsAsking(false);
      }
    },
    [isAsking, selectedDocumentId, topK]
  );

  const clearChat = useCallback(() => {
    setMessages([]);
    setError(null);
  }, []);

  return {
    messages,
    isAsking,
    error,
    selectedDocumentId,
    setSelectedDocumentId,
    topK,
    setTopK,
    askQuestion,
    clearChat,
  };
}
