import { IChatSession, IChatMessage } from "../types";
import { CitationModel } from "./CitationModel";

export class ChatMessageModel {
  readonly messageId: string;
  readonly sessionId: string;
  readonly role: "user" | "assistant";
  readonly content: string;
  readonly citations: CitationModel[];
  readonly createdAt: Date;

  constructor(dto: IChatMessage) {
    this.messageId = dto.message_id;
    this.sessionId = dto.session_id;
    this.role = dto.role;
    this.content = dto.content;
    this.citations = (dto.citations || []).map((c) => CitationModel.fromJson(c));
    this.createdAt = new Date(dto.created_at);
  }

  get isUser(): boolean {
    return this.role === "user";
  }

  get isAssistant(): boolean {
    return this.role === "assistant";
  }

  get formattedTime(): string {
    return this.createdAt.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
  }
}

export class ChatSessionModel {
  readonly sessionId: string;
  readonly title: string;
  readonly createdAt: Date;
  readonly updatedAt: Date;
  readonly messageCount: number;

  constructor(dto: IChatSession) {
    this.sessionId = dto.session_id;
    this.title = dto.title;
    this.createdAt = new Date(dto.created_at);
    this.updatedAt = new Date(dto.updated_at);
    this.messageCount = dto.message_count;
  }

  get relativeTime(): string {
    const diffMs = Date.now() - this.updatedAt.getTime();
    const diffMins = Math.floor(diffMs / (1000 * 60));
    if (diffMins < 1) return "Just now";
    if (diffMins < 60) return `${diffMins}m ago`;
    const diffHours = Math.floor(diffMins / 60);
    if (diffHours < 24) return `${diffHours}h ago`;
    return `${Math.floor(diffHours / 24)}d ago`;
  }
}
