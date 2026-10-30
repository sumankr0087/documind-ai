import { AbstractHttpService } from "./AbstractHttpService";
import { IChatSession, IChatSessionListResponse, IChatSessionDetailResponse } from "../types";
import { ChatSessionModel, ChatMessageModel } from "../models";

export class ChatService extends AbstractHttpService {
  public async listSessions(): Promise<ChatSessionModel[]> {
    const data = await this.get<IChatSessionListResponse>("/chat/sessions");
    return data.sessions.map((s) => new ChatSessionModel(s));
  }

  public async createSession(title: string = "New Chat"): Promise<ChatSessionModel> {
    const data = await this.post<IChatSession>("/chat/sessions", { title });
    return new ChatSessionModel(data);
  }

  public async getSession(sessionId: string): Promise<{ session: ChatSessionModel; messages: ChatMessageModel[] }> {
    const data = await this.get<IChatSessionDetailResponse>(`/chat/sessions/${sessionId}`);
    return {
      session: new ChatSessionModel(data.session),
      messages: data.messages.map((m) => new ChatMessageModel(m)),
    };
  }

  public async deleteSession(sessionId: string): Promise<void> {
    await this.delete(`/chat/sessions/${sessionId}`);
  }
}
