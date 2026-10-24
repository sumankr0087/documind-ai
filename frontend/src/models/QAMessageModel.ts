import { IQuestionResponse } from "../types";
import { CitationModel } from "./CitationModel";

export type MessageSender = "user" | "assistant" | "system";

/**
 * Domain entity model representing a message in the Q&A thread.
 */
export class QAMessageModel {
  readonly id: string;
  readonly sender: MessageSender;
  readonly text: string;
  readonly timestamp: Date;
  readonly citations: CitationModel[];
  readonly evidenceSufficient: boolean;
  readonly modelUsed?: string;
  readonly scopedDocId?: string | null;
  readonly isError?: boolean;

  constructor(
    id: string,
    sender: MessageSender,
    text: string,
    timestamp: Date,
    citations: CitationModel[] = [],
    evidenceSufficient: boolean = true,
    modelUsed?: string,
    scopedDocId?: string | null,
    isError: boolean = false
  ) {
    this.id = id;
    this.sender = sender;
    this.text = text;
    this.timestamp = timestamp;
    this.citations = citations;
    this.evidenceSufficient = evidenceSufficient;
    this.modelUsed = modelUsed;
    this.scopedDocId = scopedDocId;
    this.isError = isError;
  }

  public static createUserMessage(question: string, scopedDocId?: string | null): QAMessageModel {
    return new QAMessageModel(
      `msg_user_${Date.now()}_${Math.random().toString(36).substr(2, 5)}`,
      "user",
      question,
      new Date(),
      [],
      true,
      undefined,
      scopedDocId
    );
  }

  public static createAssistantMessage(dto: IQuestionResponse): QAMessageModel {
    const citations = (dto.citations || []).map((c) => CitationModel.fromJson(c));
    return new QAMessageModel(
      `msg_asst_${Date.now()}_${Math.random().toString(36).substr(2, 5)}`,
      "assistant",
      dto.answer,
      new Date(),
      citations,
      dto.evidence_sufficient,
      dto.model_used,
      dto.document_id
    );
  }

  public static createErrorMessage(errorText: string): QAMessageModel {
    return new QAMessageModel(
      `msg_err_${Date.now()}_${Math.random().toString(36).substr(2, 5)}`,
      "system",
      errorText,
      new Date(),
      [],
      false,
      undefined,
      undefined,
      true
    );
  }

  public hasCitations(): boolean {
    return this.citations.length > 0;
  }

  public isInsufficientEvidence(): boolean {
    return this.sender === "assistant" && !this.evidenceSufficient;
  }
}
