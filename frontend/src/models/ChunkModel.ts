import { IChunkMetadata, IChunkDetail } from "../types";

/**
 * Domain entity model representing an individual indexed chunk of a document.
 */
export class ChunkModel {
  readonly chunkId: string;
  readonly documentId: string;
  readonly chunkIndex: number;
  readonly filename: string;
  readonly pageNumber: number | null;
  readonly charLength: number;
  readonly text?: string;

  constructor(
    chunkId: string,
    documentId: string,
    chunkIndex: number,
    filename: string,
    pageNumber: number | null,
    charLength: number,
    text?: string
  ) {
    this.chunkId = chunkId;
    this.documentId = documentId;
    this.chunkIndex = chunkIndex;
    this.filename = filename;
    this.pageNumber = pageNumber;
    this.charLength = charLength;
    this.text = text;
  }

  public static fromJson(dto: IChunkMetadata | IChunkDetail): ChunkModel {
    return new ChunkModel(
      dto.chunk_id,
      dto.document_id,
      dto.chunk_index,
      dto.filename,
      dto.page_number,
      dto.char_length,
      "text" in dto ? dto.text : undefined
    );
  }

  public getPageLabel(): string {
    return this.pageNumber !== null && this.pageNumber > 0 ? `Page ${this.pageNumber}` : "Section";
  }

  public getPreview(maxLength: number = 180): string {
    if (!this.text) return `Chunk #${this.chunkIndex} (${this.charLength} chars)`;
    if (this.text.length <= maxLength) return this.text;
    return `${this.text.slice(0, maxLength).trim()}...`;
  }
}
