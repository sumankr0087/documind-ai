import { AbstractHttpService } from "./AbstractHttpService";
import {
  IDocumentUploadResponse,
  IDocumentListResponse,
  IDocumentDetailResponse,
  IDocumentDeleteResponse,
} from "../types";
import { DocumentModel, ChunkModel } from "../models";

export interface IDocumentService {
  uploadDocument(file: File): Promise<DocumentModel>;
  listDocuments(): Promise<DocumentModel[]>;
  getDocument(documentId: string): Promise<{ document: DocumentModel; chunks: ChunkModel[] }>;
  deleteDocument(documentId: string): Promise<{ success: boolean; chunksDeleted: number; message: string }>;
}

/**
 * Concrete OOP service managing document ingestion and storage operations.
 */
export class DocumentService extends AbstractHttpService implements IDocumentService {
  constructor(baseUrl: string = "") {
    super(baseUrl);
  }

  public async uploadDocument(file: File): Promise<DocumentModel> {
    const formData = new FormData();
    formData.append("file", file);

    const response = await this.postFormData<IDocumentUploadResponse>("/documents/upload", formData);
    return DocumentModel.fromJson(response.document);
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
