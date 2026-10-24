import { AbstractHttpService } from "./AbstractHttpService";
import { IQuestionRequest, IQuestionResponse } from "../types";
import { QAMessageModel } from "../models";

export interface IQuestionService {
  askQuestion(question: string, documentId?: string | null, topK?: number): Promise<QAMessageModel>;
}

/**
 * Concrete OOP service managing RAG Question Answering operations.
 */
export class QuestionService extends AbstractHttpService implements IQuestionService {
  constructor(baseUrl: string = "") {
    super(baseUrl);
  }

  public async askQuestion(
    question: string,
    documentId?: string | null,
    topK: number = 5
  ): Promise<QAMessageModel> {
    const payload: IQuestionRequest = {
      question: question.trim(),
      document_id: documentId || null,
      top_k: topK,
    };

    const response = await this.post<IQuestionResponse>("/questions/ask", payload);
    return QAMessageModel.createAssistantMessage(response);
  }
}
