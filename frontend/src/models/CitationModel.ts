import { ICitation } from "../types";

/**
 * Domain entity model representing a grounded citation returned with an answer.
 */
export class CitationModel {
  readonly chunkId: string;
  readonly documentId: string;
  readonly filename: string;
  readonly pageNumber: number | null;
  readonly snippet: string;
  readonly relevanceScore: number;

  constructor(
    chunkId: string,
    documentId: string,
    filename: string,
    pageNumber: number | null,
    snippet: string,
    relevanceScore: number
  ) {
    this.chunkId = chunkId;
    this.documentId = documentId;
    this.filename = filename;
    this.pageNumber = pageNumber;
    this.snippet = snippet;
    this.relevanceScore = relevanceScore;
  }

  public static fromJson(dto: ICitation): CitationModel {
    return new CitationModel(
      dto.chunk_id,
      dto.document_id,
      dto.filename,
      dto.page_number,
      dto.snippet,
      dto.relevance_score
    );
  }

  public getConfidencePercentage(): string {
    const pct = Math.round(this.relevanceScore * 100);
    return `${pct}% match`;
  }

  public getConfidenceLevel(): "high" | "medium" | "low" {
    if (this.relevanceScore >= 0.75) return "high";
    if (this.relevanceScore >= 0.5) return "medium";
    return "low";
  }

  public getConfidenceColor(): { text: string; bg: string; border: string } {
    switch (this.getConfidenceLevel()) {
      case "high":
        return { text: "#059669", bg: "#ecfdf5", border: "#a7f3d0" };
      case "medium":
        return { text: "#d97706", bg: "#fffbeb", border: "#fde68a" };
      case "low":
      default:
        return { text: "#6b7280", bg: "#f3f4f6", border: "#e5e7eb" };
    }
  }

  public getPageLabel(): string {
    return this.pageNumber !== null && this.pageNumber > 0 ? `Page ${this.pageNumber}` : "General Context";
  }
}
