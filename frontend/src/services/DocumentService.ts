import { AbstractHttpService } from "./AbstractHttpService";
import {
  IDocumentUploadResponse,
  IBatchUploadResponse,
  IDocumentListResponse,
  IDocumentDetailResponse,
  IDocumentDeleteResponse,
} from "../types";
import { DocumentModel, ChunkModel } from "../models";

export interface IDocumentService {
  uploadDocument(file: File): Promise<{ document: DocumentModel; skipped: boolean; message: string }>;
  uploadBatch(files: File[]): Promise<{ documents: DocumentModel[]; total: number; ingested: number; skipped: number }>;
  listDocuments(): Promise<DocumentModel[]>;
  getDocument(documentId: string): Promise<{ document: DocumentModel; chunks: ChunkModel[] }>;
  deleteDocument(documentId: string): Promise<{ success: boolean; chunksDeleted: number; message: string }>;
}

/**
 * Concrete OOP service managing document ingestion and storage operations with duplicate detection.
 */
export class DocumentService extends AbstractHttpService implements IDocumentService {
  constructor(baseUrl: string = "") {
    super(baseUrl);
  }

  public async uploadDocument(
    file: File
  ): Promise<{ document: DocumentModel; skipped: boolean; message: string }> {
    const formData = new FormData();
    formData.append("file", file);

    const response = await this.postFormData<IDocumentUploadResponse>("/documents/upload", formData);
    return {
      document: DocumentModel.fromJson(response.document),
      skipped: Boolean(response.skipped),
      message: response.message,
    };
  }

  public async uploadBatch(
    files: File[]
  ): Promise<{ documents: DocumentModel[]; total: number; ingested: number; skipped: number }> {
    const formData = new FormData();
    for (const file of files) {
      formData.append("files", file);
    }

    const response = await this.postFormData<IBatchUploadResponse>("/documents/upload-batch", formData);
    return {
      documents: (response.documents || []).map((d) => DocumentModel.fromJson(d)),
      total: response.total_files,
      ingested: response.ingested_count,
      skipped: response.skipped_count,
    };
  }

  public async listDocuments(): Promise<DocumentModel[]> {
    const response = await this.get<IDocumentListResponse>("/documents");
    return (response.documents || []).map((doc) => DocumentModel.fromJson(doc));
  }

  public async getDocument(
    documentId: string
  ): Promise<{ document: DocumentModel; chunks: ChunkModel[] }> {
    const response = await this.get<IDocumentDetailResponse>(`/documents/${documentId}`);
    return {
      document: DocumentModel.fromJson(response.document),
      chunks: (response.chunks || []).map((chunk) => ChunkModel.fromJson(chunk)),
    };
  }

  public async deleteDocument(
    documentId: string
  ): Promise<{ success: boolean; chunksDeleted: number; message: string }> {
    const response = await this.delete<IDocumentDeleteResponse>(`/documents/${documentId}`);
    return {
      success: true,
      chunksDeleted: response.chunks_deleted,
      message: response.message,
    };
  }
}
