"use client";

import { useCallback, useRef, useState } from "react";
import { Upload, FileText, X, AlertCircle, CheckCircle2 } from "lucide-react";
import { resumesApi, ApiError } from "@/lib/api";
import { cn } from "@/lib/utils";
import { RecommendationPipeline, usePipelineProgress } from "./recommendation-pipeline";
import type { ResumeData } from "@/lib/types";

interface ResumeUploadZoneProps {
  onSuccess: (data: ResumeData) => void;
}

export function ResumeUploadZone({ onSuccess }: ResumeUploadZoneProps) {
  const [isDragOver, setIsDragOver] = useState(false);
  const [file, setFile] = useState<File | null>(null);
  const [uploadPct, setUploadPct] = useState(0);
  const [isUploading, setIsUploading] = useState(false);
  const [isComplete, setIsComplete] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  const pipelineStep = usePipelineProgress(isUploading, uploadPct, isComplete);

  function validateFile(f: File): string | null {
    if (!f.name.toLowerCase().endsWith(".pdf")) return "Only PDF files are supported.";
    if (f.size > 10 * 1024 * 1024) return "File must be under 10 MB.";
    return null;
  }

  const startUpload = useCallback(async (f: File) => {
    setError(null);
    setFile(f);
    setIsUploading(true);
    setIsComplete(false);
    setUploadPct(0);

    try {
      const result = await resumesApi.upload(f, (pct) => setUploadPct(pct));

      setIsComplete(true);
      setIsUploading(false);

      // Convert response to ResumeData shape
      const resumeData: ResumeData = {
        name: (result.resume as { name?: string }).name ?? null,
        resume: result.resume,
        queries: result.search_queries,
      };
      onSuccess(resumeData);
    } catch (err) {
      setIsUploading(false);
      setIsComplete(false);
      setFile(null);
      setError(err instanceof ApiError ? err.detail : "Upload failed. Please try again.");
    }
  }, [onSuccess]);

  const handleFiles = useCallback(
    (files: FileList | null) => {
      if (!files || files.length === 0) return;
      const f = files[0];
      const validationError = validateFile(f);
      if (validationError) {
        setError(validationError);
        return;
      }
      startUpload(f);
    },
    [startUpload]
  );

  function onDrop(e: React.DragEvent) {
    e.preventDefault();
    setIsDragOver(false);
    handleFiles(e.dataTransfer.files);
  }

  function onDragOver(e: React.DragEvent) {
    e.preventDefault();
    setIsDragOver(true);
  }

  function onDragLeave() {
    setIsDragOver(false);
  }

  function onInputChange(e: React.ChangeEvent<HTMLInputElement>) {
    handleFiles(e.target.files);
    e.target.value = "";
  }

  // Show pipeline when uploading/complete
  if (isUploading || isComplete) {
    return (
      <div className="space-y-4">
        {file && (
          <div className="flex items-center gap-3 rounded-xl border border-line bg-surface px-4 py-3 dark:border-line-dark dark:bg-surface-dark">
            <FileText className="h-4 w-4 shrink-0 text-signal" />
            <div className="flex-1 min-w-0">
              <p className="truncate text-[13px] font-medium text-ink dark:text-ink-dark">
                {file.name}
              </p>
              <p className="text-[11.5px] text-muted dark:text-muted-dark">
                {(file.size / 1024).toFixed(0)} KB
              </p>
            </div>
            {isUploading && (
              <div className="flex items-center gap-2 text-[12px] text-muted dark:text-muted-dark">
                <div className="h-1 w-20 overflow-hidden rounded-full bg-line dark:bg-line-dark">
                  <div
                    className="h-full rounded-full bg-signal transition-all duration-300"
                    style={{ width: `${uploadPct}%` }}
                  />
                </div>
                {uploadPct}%
              </div>
            )}
            {isComplete && (
              <CheckCircle2 className="h-4 w-4 text-signal" />
            )}
          </div>
        )}

        <RecommendationPipeline
          currentStep={pipelineStep}
          complete={isComplete}
        />

        {/* Info notice about recommendation matching */}
        {isComplete && (
          <div className="flex items-start gap-2.5 rounded-lg border border-signal/20 bg-signal-soft/40 px-4 py-3 dark:bg-signal-soft-dark/30">
            <span className="mt-0.5 text-[13px]">🔍</span>
            <p className="text-[12.5px] leading-relaxed text-muted dark:text-muted-dark">
              We&apos;re finding the best matches from our current database. New opportunities
              will be included during the next scheduled scan.
            </p>
          </div>
        )}
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {/* Drop zone */}
      <div
        onDrop={onDrop}
        onDragOver={onDragOver}
        onDragLeave={onDragLeave}
        onClick={() => inputRef.current?.click()}
        role="button"
        tabIndex={0}
        aria-label="Upload resume — drag and drop or click to browse"
        onKeyDown={(e) => e.key === "Enter" && inputRef.current?.click()}
        className={cn(
          "flex cursor-pointer flex-col items-center gap-5 rounded-xl2 border-2 border-dashed px-8 py-14 text-center transition-all duration-200",
          isDragOver
            ? "border-signal/60 bg-signal-soft dark:bg-signal-soft-dark"
            : "border-line bg-surface hover:border-signal/30 hover:bg-signal-soft/40 dark:border-line-dark dark:bg-surface-dark dark:hover:bg-signal-soft-dark/40"
        )}
      >
        <div
          className={cn(
            "flex h-14 w-14 items-center justify-center rounded-2xl border transition-colors duration-200",
            isDragOver
              ? "border-signal/30 bg-signal-soft dark:bg-signal-soft-dark"
              : "border-line bg-paper dark:border-line-dark dark:bg-paper-dark"
          )}
        >
          <Upload
            className={cn(
              "h-6 w-6 transition-colors duration-200",
              isDragOver ? "text-signal" : "text-muted dark:text-muted-dark"
            )}
            strokeWidth={1.75}
          />
        </div>

        <div>
          <p className="font-display text-[16px] font-medium text-ink dark:text-ink-dark">
            {isDragOver ? "Drop your resume here" : "Upload your resume"}
          </p>
          <p className="mt-1.5 text-[13.5px] text-muted dark:text-muted-dark">
            Drag & drop a PDF, or{" "}
            <span className="text-ink underline-offset-2 hover:underline dark:text-ink-dark">
              browse files
            </span>
          </p>
          <p className="mt-1 text-[11.5px] text-muted/70 dark:text-muted-dark/70">
            PDF only · Max 10 MB
          </p>
        </div>
      </div>

      <input
        ref={inputRef}
        type="file"
        accept=".pdf,application/pdf"
        className="hidden"
        onChange={onInputChange}
        aria-hidden="true"
      />

      {/* Error */}
      {error && (
        <div className="flex items-start gap-2.5 rounded-lg border border-danger/20 bg-danger/5 px-4 py-3">
          <AlertCircle className="mt-0.5 h-4 w-4 shrink-0 text-danger" />
          <div className="flex-1">
            <p className="text-[13px] text-danger">{error}</p>
          </div>
          <button
            onClick={() => setError(null)}
            className="text-danger/60 hover:text-danger"
          >
            <X className="h-3.5 w-3.5" />
          </button>
        </div>
      )}
    </div>
  );
}
