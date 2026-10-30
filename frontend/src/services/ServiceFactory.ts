import { DocumentService, IDocumentService } from "./DocumentService";
import { QuestionService, IQuestionService } from "./QuestionService";
import { HealthService, IHealthService } from "./HealthService";
import { ChatService } from "./ChatService";

/**
 * Singleton ServiceFactory managing dependency injection of API services.
 */
export class ServiceFactory {
  private static instance: ServiceFactory | null = null;
  private readonly baseUrl: string;

  private documentService: IDocumentService | null = null;
  private questionService: IQuestionService | null = null;
  private healthService: IHealthService | null = null;
  private chatService: ChatService | null = null;

  private constructor(baseUrl: string = "") {
    this.baseUrl = baseUrl;
  }

  public static getInstance(baseUrl: string = ""): ServiceFactory {
    if (!ServiceFactory.instance) {
      ServiceFactory.instance = new ServiceFactory(baseUrl);
    }
    return ServiceFactory.instance;
  }

  public getDocumentService(): IDocumentService {
    if (!this.documentService) {
      this.documentService = new DocumentService(this.baseUrl);
    }
    return this.documentService;
  }

  public getQuestionService(): IQuestionService {
    if (!this.questionService) {
      this.questionService = new QuestionService(this.baseUrl);
    }
    return this.questionService;
  }

  public getHealthService(): IHealthService {
    if (!this.healthService) {
      this.healthService = new HealthService(this.baseUrl);
    }
    return this.healthService;
  }

  public getChatService(): ChatService {
    if (!this.chatService) {
      this.chatService = new ChatService(this.baseUrl);
    }
    return this.chatService;
  }
}
