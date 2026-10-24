import { IDocumentMetadata } from "../types";

/**
 * Domain entity model representing an uploaded document.
 * Encapsulates presentation formatting and helper methods.
 */
export class DocumentModel {
  readonly id: string;
  readonly filename: string;
  readonly contentType: string;
  readonly sizeBytes: number;
  readonly chunkCount: number;
  readonly pageCount: number | null;
  readonly createdAt: Date;

  constructor(
    id: string,
    filename: string,
    contentType: string,
    sizeBytes: number,
    chunkCount: number,
    pageCount: number | null,
    createdAt: Date | string
  ) {
    this.id = id;
    this.filename = filename;
    this.contentType = contentType;
    this.sizeBytes = sizeBytes;
    this.chunkCount = chunkCount;
    this.pageCount = pageCount;
    this.createdAt = typeof createdAt === "string" ? new Date(createdAt) : createdAt;
  }

  /**
   * Factory method to instantiate DocumentModel from API response JSON.
   */
  public static fromJson(dto: IDocumentMetadata): DocumentModel {
    return new DocumentModel(
      dto.document_id,
      dto.filename,
      dto.content_type,
      dto.size_bytes,
      dto.chunk_count,
      dto.page_count,
      dto.created_at
    );
  }

  /**
   * Return formatted human-readable file size (e.g., 256.4 KB, 1.2 MB).
   */
  public getFormattedSize(): string {
    if (this.sizeBytes === 0) return "0 B";
    const k = 1024;
    const sizes = ["B", "KB", "MB", "GB"];
    const i = Math.floor(Math.log(this.sizeBytes) / Math.log(k));
    return `${parseFloat((this.sizeBytes / Math.pow(k, i)).toFixed(1))} ${sizes[i]}`;
  }

  /**
   * Return formatted relative or localized timestamp.
   */
  public getFormattedDate(): string {
    return this.createdAt.toLocaleDateString("en-US", {
      month: "short",
      day: "numeric",
      hour: "2-digit",
      minute: "2-digit",
    });
  }

  /**
   * Extract lowercase file extension without dot.
   */
  public getExtension(): string {
    const parts = this.filename.split(".");
    return parts.length > 1 ? parts[parts.length - 1].toLowerCase() : "txt";
  }

  /**
   * Return standardized badge label according to format.
   */
  public getFormatBadge(): { label: string; color: string; bg: string } {
    const ext = this.getExtension();
    switch (ext) {
      case "pdf":
        return { label: "PDF", color: "#ef4444", bg: "#fef2f2" };
      case "md":
      case "markdown":
        return { label: "Markdown", color: "#3b82f6", bg: "#eff6ff" };
      case "txt":
      default:
        return { label: "Plain Text", color: "#10b981", bg: "#ecfdf5" };
    }
  }

  public isPdf(): boolean {
    return this.getExtension() === "pdf";
  }
}
