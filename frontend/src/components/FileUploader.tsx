import React, { useState, useRef } from "react";
import { UploadCloud, FileText, Loader2, AlertCircle, Files } from "lucide-react";

interface FileUploaderProps {
  onUpload: (file: File) => Promise<unknown>;
  onBatchUpload?: (files: File[]) => Promise<unknown>;
  uploading: boolean;
  uploadStatus?: string | null;
}

const SUPPORTED_EXTS = [".pdf", ".txt", ".md", ".markdown"];
const MAX_SIZE_MB = 25;

export const FileUploader: React.FC<FileUploaderProps> = ({
  onUpload,
  onBatchUpload,
  uploading,
  uploadStatus,
}) => {
  const [isDragOver, setIsDragOver] = useState(false);
  const [localError, setLocalError] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const processFiles = async (fileList: FileList | File[]) => {
    setLocalError(null);
    const validFiles: File[] = [];

    for (let i = 0; i < fileList.length; i++) {
      const file = fileList[i];
      if (file.size > MAX_SIZE_MB * 1024 * 1024) {
        setLocalError(`File '${file.name}' (${(file.size / 1024 / 1024).toFixed(1)}MB) exceeds ${MAX_SIZE_MB}MB.`);
        return;
      }
      const nameLower = file.name.toLowerCase();
      const isSupported = SUPPORTED_EXTS.some((ext) => nameLower.endsWith(ext));
      if (!isSupported) {
        setLocalError(`Unsupported format '${file.name}'. Please upload PDF, Markdown, or TXT.`);
        return;
      }
      validFiles.push(file);
    }

    if (validFiles.length === 0) return;

    if (validFiles.length > 1 && onBatchUpload) {
      await onBatchUpload(validFiles);
    } else {
      for (const f of validFiles) {
        await onUpload(f);
      }
    }

    if (fileInputRef.current) {
      fileInputRef.current.value = "";
    }
  };

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragOver(true);
  };

  const handleDragLeave = () => {
    setIsDragOver(false);
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragOver(false);
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      processFiles(e.dataTransfer.files);
    }
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files.length > 0) {
      processFiles(e.target.files);
    }
  };

  return (
    <div className="file-uploader-card">
      <div
        className={`dropzone ${isDragOver ? "drag-over" : ""} ${uploading ? "uploading" : ""}`}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
        onClick={() => !uploading && fileInputRef.current?.click()}
      >
        <input
          ref={fileInputRef}
          type="file"
          accept=".pdf,.txt,.md,.markdown"
          multiple
          className="hidden"
          onChange={handleFileChange}
          disabled={uploading}
        />

        {uploading ? (
          <div className="dropzone-content">
            <Loader2 size={32} className="spin-icon text-indigo-600 mb-2" />
            <p className="font-semibold text-slate-800 text-sm">Processing &amp; Indexing Document(s)...</p>
            <p className="text-xs text-slate-500 mt-1">
              Extracting text &bull; Checking duplicates &bull; Generating embeddings &bull; ChromaDB
            </p>
          </div>
        ) : (
          <div className="dropzone-content">
            <div className="upload-icon-circle">
              <UploadCloud size={24} className="text-indigo-600" />
            </div>
            <p className="font-semibold text-slate-800 text-sm">
              Drop single or multiple files, or <span className="text-indigo-600 underline">browse</span>
            </p>
            <div className="flex items-center gap-2 mt-2 text-xs text-slate-400">
              <span className="flex items-center gap-1">
                <FileText size={12} /> PDF (PyMuPDF)
              </span>
              <span>&bull;</span>
              <span>Markdown</span>
              <span>&bull;</span>
              <span>Plain Text</span>
              <span>&bull;</span>
              <span className="flex items-center gap-1 font-medium text-indigo-500">
                <Files size={12} /> Multi-file Upload
              </span>
            </div>
          </div>
        )}
      </div>

      {uploadStatus && (
        <div className="mt-2 text-xs text-indigo-600 bg-indigo-50 px-3 py-1.5 rounded border border-indigo-100 flex items-center gap-1.5">
          <span>ℹ️ {uploadStatus}</span>
        </div>
      )}

      {localError && (
        <div className="upload-error-banner">
          <AlertCircle size={14} className="shrink-0" />
          <span>{localError}</span>
        </div>
      )}
    </div>
  );
};
