import { AbstractHttpService } from "./AbstractHttpService";
import { IQuestionRequest, IQuestionResponse } from "../types";
import { QAMessageModel } from "../models";

export interface IAskQuestionParams {
  question: string;
  documentId?: string | null;
  documentIds?: string[] | null;
  sessionId?: string | null;
  fileExtensions?: string[] | null;
  topK?: number;
  enableMmr?: boolean;
  enableHybrid?: boolean;
  enableReranking?: boolean;
}

export interface IQuestionService {
  askQuestion(params: IAskQuestionParams): Promise<QAMessageModel>;
  askQuestionStream(
    params: IAskQuestionParams,
    onToken: (delta: string) => void,
    onDone: (response: QAMessageModel) => void,
    onError: (error: Error) => void
  ): Promise<void>;
}

/**
 * Concrete OOP service managing RAG Question Answering operations including SSE streaming.
 */
export class QuestionService extends AbstractHttpService implements IQuestionService {
  constructor(baseUrl: string = "") {
    super(baseUrl);
  }

  public async askQuestion(params: IAskQuestionParams): Promise<QAMessageModel> {
    const payload: IQuestionRequest = {
      question: params.question.trim(),
      document_id: params.documentId || null,
      document_ids: params.documentIds && params.documentIds.length > 0 ? params.documentIds : null,
      session_id: params.sessionId || null,
      file_extensions: params.fileExtensions || null,
      top_k: params.topK || 5,
      enable_mmr: params.enableMmr,
      enable_hybrid: params.enableHybrid,
      enable_reranking: params.enableReranking,
    };

    const response = await this.post<IQuestionResponse>("/questions/ask", payload);
    return QAMessageModel.createAssistantMessage(response);
  }

  public async askQuestionStream(
    params: IAskQuestionParams,
    onToken: (delta: string) => void,
    onDone: (response: QAMessageModel) => void,
    onError: (error: Error) => void
  ): Promise<void> {
    const payload: IQuestionRequest = {
      question: params.question.trim(),
      document_id: params.documentId || null,
      document_ids: params.documentIds && params.documentIds.length > 0 ? params.documentIds : null,
      session_id: params.sessionId || null,
      file_extensions: params.fileExtensions || null,
      top_k: params.topK || 5,
      enable_mmr: params.enableMmr,
      enable_hybrid: params.enableHybrid,
      enable_reranking: params.enableReranking,
    };

    try {
      const response = await fetch(`${this.baseUrl}/questions/ask-stream`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Accept: "text/event-stream",
        },
        body: JSON.stringify(payload),
      });

      if (!response.ok) {
        throw new Error(`Streaming failed with HTTP status ${response.status}: ${response.statusText}`);
      }

      const reader = response.body?.getReader();
      if (!reader) {
        throw new Error("Response body is not readable for streaming");
      }

      const decoder = new TextDecoder("utf-8");
      let buffer = "";

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split("\n\n");
        buffer = lines.pop() || "";

        for (const block of lines) {
          const trimmed = block.trim();
          if (trimmed.startsWith("data: ")) {
            const jsonStr = trimmed.slice(6);
            try {
              const event = JSON.parse(jsonStr);
              if (event.type === "token") {
                onToken(event.delta);
              } else if (event.type === "done") {
                const qaResponse: IQuestionResponse = {
                  question: params.question,
                  answer: event.answer,
                  citations: event.citations || [],
                  evidence_sufficient: event.evidence_sufficient ?? true,
                  document_id: params.documentId || null,
                  document_ids: params.documentIds || null,
                  session_id: params.sessionId || null,
                  model_used: event.model_used || "DocuMind-Engine",
                };
                onDone(QAMessageModel.createAssistantMessage(qaResponse));
              } else if (event.type === "error") {
                throw new Error(event.detail || "Streaming error from LLM engine");
              }
            } catch (err) {
              console.warn("Failed to parse SSE event:", jsonStr, err);
            }
          }
        }
      }
    } catch (err: any) {
      onError(err instanceof Error ? err : new Error(String(err)));
    }
  }
}
