import { IHealthResponse } from "../types";

/**
 * Domain entity model representing backend system health and connected subsystems.
 */
export class SystemHealthModel {
  readonly status: string;
  readonly version: string;
  readonly appEnv: string;
  readonly vectorStoreConnected: boolean;
  readonly vectorStoreStatus: string;
  readonly collectionName: string;
  readonly totalChunks: number;
  readonly embeddingModel: string;
  readonly embeddingDevice: string;
  readonly llmProvider: string;
  readonly llmModel: string;
  readonly llmConfigured: boolean;

  constructor(
    status: string,
    version: string,
    appEnv: string,
    vectorStoreConnected: boolean,
    vectorStoreStatus: string,
    collectionName: string,
    totalChunks: number,
    embeddingModel: string,
    embeddingDevice: string,
    llmProvider: string,
    llmModel: string,
    llmConfigured: boolean
  ) {
    this.status = status;
    this.version = version;
    this.appEnv = appEnv;
    this.vectorStoreConnected = vectorStoreConnected;
    this.vectorStoreStatus = vectorStoreStatus;
    this.collectionName = collectionName;
    this.totalChunks = totalChunks;
    this.embeddingModel = embeddingModel;
    this.embeddingDevice = embeddingDevice;
    this.llmProvider = llmProvider;
    this.llmModel = llmModel;
    this.llmConfigured = llmConfigured;
  }

  public static fromJson(dto: IHealthResponse): SystemHealthModel {
    const vsStatus = dto.services?.vector_store?.status || "disconnected";
    const vsConnected = vsStatus === "connected";
    const totalChunks = dto.services?.vector_store?.total_chunks ?? 0;
    const collectionName = dto.services?.vector_store?.collection || "documind_collection";
    const embModel = dto.services?.embedding?.model || "sentence-transformers";
    const embDevice = dto.services?.embedding?.device || "cpu";
    const llmProv = dto.services?.llm?.provider || "openai";
    const llmMod = dto.services?.llm?.model || "default";
    const llmConf = dto.services?.llm?.configured ?? false;

    return new SystemHealthModel(
      dto.status,
      dto.version,
      dto.app_env,
      vsConnected,
      vsStatus,
      collectionName,
      totalChunks,
      embModel,
      embDevice,
      llmProv,
      llmMod,
      llmConf
    );
  }

  public isHealthy(): boolean {
    return this.status === "healthy" && this.vectorStoreConnected;
  }

  public getStatusBadge(): { text: string; bg: string; dot: string } {
    if (this.isHealthy()) {
      return { text: "Operational", bg: "#ecfdf5", dot: "#10b981" };
    }
    return { text: "Degraded", bg: "#fffbeb", dot: "#f59e0b" };
  }
}
