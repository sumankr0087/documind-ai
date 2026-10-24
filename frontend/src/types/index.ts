/**
 * Core type declarations and DTO interfaces representing backend payloads.
 */

export interface IDocumentMetadata {
  document_id: string;
  filename: string;
  content_type: string;
  size_bytes: number;
  chunk_count: number;
  page_count: number | null;
  created_at: string;
}

export interface IChunkMetadata {
  chunk_id: string;
  document_id: string;
  chunk_index: number;
  filename: string;
  page_number: number | null;
  char_length: number;
}

export interface IChunkDetail extends IChunkMetadata {
  text?: string;
}

export interface ICitation {
  chunk_id: string;
  document_id: string;
  filename: string;
  page_number: number | null;
  snippet: string;
  relevance_score: number;
}

export interface IQuestionRequest {
  question: string;
  document_id?: string | null;
  top_k?: number;
}

export interface IQuestionResponse {
  question: string;
  answer: string;
  citations: ICitation[];
  evidence_sufficient: boolean;
  document_id: string | null;
  model_used: string;
}

export interface IHealthServices {
  vector_store: {
    status: string;
    collection: string;
    total_chunks: number;
  };
  embedding: {
    model: string;
    device: string;
  };
  llm: {
    provider: string;
    model: string;
    configured: boolean;
  };
}

export interface IHealthResponse {
  status: string;
  version: string;
  app_env: string;
  services: IHealthServices;
}

export interface IDocumentUploadResponse {
  message: string;
  document: IDocumentMetadata;
}

export interface IDocumentListResponse {
  total_documents: number;
  documents: IDocumentMetadata[];
}

export interface IDocumentDetailResponse {
  document: IDocumentMetadata;
  chunks: IChunkMetadata[];
}

export interface IDocumentDeleteResponse {
  message: string;
  document_id: string;
  chunks_deleted: number;
}
