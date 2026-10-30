import { useState, useEffect, useCallback } from "react";
import { DocumentModel, ChunkModel } from "../models";
import { ServiceFactory, ApiException } from "../services";

export function useDocuments() {
  const [documents, setDocuments] = useState<DocumentModel[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [uploading, setUploading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [uploadStatus, setUploadStatus] = useState<string | null>(null);

  // For Document inspection modal
  const [inspectingDoc, setInspectingDoc] = useState<{
    document: DocumentModel;
    chunks: ChunkModel[];
  } | null>(null);
  const [inspectLoading, setInspectLoading] = useState<boolean>(false);

  const fetchDocuments = useCallback(async () => {
    try {
      setLoading(true);
      const docService = ServiceFactory.getInstance().getDocumentService();
      const docs = await docService.listDocuments();
      setDocuments(docs);
      setError(null);
    } catch (err: unknown) {
      const msg = err instanceof ApiException ? err.getDisplayMessage() : "Failed to load documents";
      setError(msg);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchDocuments();
  }, [fetchDocuments]);

  const uploadDocument = async (file: File): Promise<DocumentModel | null> => {
    try {
      setUploading(true);
      setError(null);
      setUploadStatus(null);
      const docService = ServiceFactory.getInstance().getDocumentService();
      const res = await docService.uploadDocument(file);
      if (res.skipped) {
        setUploadStatus(res.message);
      } else {
        setDocuments((prev) => [res.document, ...prev.filter((d) => d.id !== res.document.id)]);
      }
      return res.document;
    } catch (err: unknown) {
      const msg = err instanceof ApiException ? err.getDisplayMessage() : "Failed to upload document";
      setError(msg);
      return null;
    } finally {
      setUploading(false);
    }
  };

  const uploadBatch = async (files: File[]): Promise<{ ingested: number; skipped: number; total: number } | null> => {
    try {
      setUploading(true);
      setError(null);
      setUploadStatus(null);
      const docService = ServiceFactory.getInstance().getDocumentService();
      const res = await docService.uploadBatch(files);
      setUploadStatus(
        `Batch upload: ${res.ingested} indexed, ${res.skipped} duplicate(s) skipped.`
      );
      await fetchDocuments();
      return res;
    } catch (err: unknown) {
      const msg = err instanceof ApiException ? err.getDisplayMessage() : "Batch upload failed";
      setError(msg);
      return null;
    } finally {
      setUploading(false);
    }
  };

  const deleteDocument = async (documentId: string): Promise<boolean> => {
    try {
      setError(null);
      const docService = ServiceFactory.getInstance().getDocumentService();
      await docService.deleteDocument(documentId);
      setDocuments((prev) => prev.filter((d) => d.id !== documentId));
      return true;
    } catch (err: unknown) {
      const msg = err instanceof ApiException ? err.getDisplayMessage() : "Failed to delete document";
      setError(msg);
      return false;
    }
  };

  const inspectDocument = async (documentId: string): Promise<void> => {
    try {
      setInspectLoading(true);
      const docService = ServiceFactory.getInstance().getDocumentService();
      const details = await docService.getDocument(documentId);
      setInspectingDoc(details);
    } catch (err: unknown) {
      const msg = err instanceof ApiException ? err.getDisplayMessage() : "Failed to inspect document chunks";
      setError(msg);
    } finally {
      setInspectLoading(false);
    }
  };

  const closeInspectModal = () => {
    setInspectingDoc(null);
  };

  return {
    documents,
    loading,
    uploading,
    uploadStatus,
    error,
    uploadDocument,
    uploadBatch,
    deleteDocument,
    inspectDocument,
    inspectingDoc,
    inspectLoading,
    closeInspectModal,
    refreshDocuments: fetchDocuments,
  };
}
