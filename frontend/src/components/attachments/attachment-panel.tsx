"use client";

import { LocalizedDateTime } from "@/components/i18n/localized-value";
import { T, confirmDelete, useI18n } from "@/components/i18n/i18n-provider";
import { useCallback, useRef, useState, type ChangeEvent } from "react";

import { Button } from "@/components/ui/button";
import { EmptyState, ErrorState, LoadingState } from "@/components/ui/page-state";
import { PaginationControls } from "@/components/ui/pagination-controls";
import { usePaginatedResource } from "@/hooks/use-paginated-resource";
import { ApiError } from "@/services/api-client";
import { attachmentService } from "@/services/attachment-service";
import type { AttachmentEntityType } from "@/types/attachment";

type AttachmentPanelProps = {
  entityId: string;
  entityType: AttachmentEntityType;
};

function getErrorMessage(error: unknown): string {
  return error instanceof ApiError ? error.message : "Unable to manage attachments.";
}

function formatFileSize(sizeBytes: number, formatNumber: (value: number | string) => string): string {
  if (sizeBytes < 1024) {
    return `${formatNumber(sizeBytes)} B`;
  }
  const kibibytes = sizeBytes / 1024;
  if (kibibytes < 1024) {
    return `${formatNumber(Number(kibibytes.toFixed(1)))} KB`;
  }
  return `${formatNumber(Number((kibibytes / 1024).toFixed(1)))} MB`;
}

export function AttachmentPanel({ entityId, entityType }: AttachmentPanelProps) {
  const { formatNumber } = useI18n();
  const inputRef = useRef<HTMLInputElement>(null);
  const [page, setPage] = useState(1);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [isUploading, setIsUploading] = useState(false);
  const [isDeletingId, setIsDeletingId] = useState<string | null>(null);
  const [actionError, setActionError] = useState<string | null>(null);
  const loadAttachments = useCallback(
    () => attachmentService.list({ entity_id: entityId, entity_type: entityType, page, page_size: 25 }),
    [entityId, entityType, page],
  );
  const { error, isLoading, items, meta, reload } = usePaginatedResource(loadAttachments);

  function selectFile(event: ChangeEvent<HTMLInputElement>) {
    setSelectedFile(event.target.files?.[0] ?? null);
    setActionError(null);
  }

  async function uploadFile() {
    if (!selectedFile) {
      setActionError("Choose a file before uploading.");
      return;
    }

    setIsUploading(true);
    setActionError(null);
    try {
      await attachmentService.upload(entityType, entityId, selectedFile);
      setSelectedFile(null);
      if (inputRef.current) {
        inputRef.current.value = "";
      }
      reload();
    } catch (caughtError) {
      setActionError(getErrorMessage(caughtError));
    } finally {
      setIsUploading(false);
    }
  }

  async function deleteAttachment(attachmentId: string, filename: string) {
    if (!confirmDelete(filename)) {
      return;
    }

    setIsDeletingId(attachmentId);
    setActionError(null);
    try {
      await attachmentService.remove(attachmentId);
      reload();
    } catch (caughtError) {
      setActionError(getErrorMessage(caughtError));
    } finally {
      setIsDeletingId(null);
    }
  }

  return (
    <section className="mt-8 border-t border-slate-100 pt-6 dark:border-slate-800" aria-labelledby="attachments-heading">
      <div className="flex flex-col gap-2 sm:flex-row sm:items-end sm:justify-between">
        <div>
          <h2 className="text-lg font-semibold text-slate-950 dark:text-white" id="attachments-heading"><T>Attachments</T></h2>
          <p className="mt-1 text-sm text-slate-500"><T>Keep source documents and supporting files with this record.</T></p>
        </div>
      </div>

      <div className="mt-5 flex flex-col gap-3 rounded-lg border border-dashed border-slate-300 p-4 dark:border-slate-700 sm:flex-row sm:items-center">
        <label className="min-w-0 flex-1"><span className="sr-only"><T>Choose an attachment</T></span><input className="crm-input block w-full text-sm text-slate-600 file:me-4 file:rounded-md file:border-0 file:bg-slate-100 file:px-3 file:py-2 file:text-sm file:font-semibold file:text-slate-700 hover:file:bg-slate-200 dark:text-slate-300 dark:file:bg-slate-900 dark:file:text-slate-200 dark:hover:file:bg-slate-800" onChange={selectFile} ref={inputRef} type="file" /></label>
        <Button disabled={!selectedFile || isUploading} onClick={() => void uploadFile()} variant="secondary">{isUploading ? <T>Uploading...</T> : <T>Upload file</T>}</Button>
      </div>
      {selectedFile ? <p className="mt-2 text-xs text-slate-500" role="status"><T>Selected:</T> {selectedFile.name} ({formatFileSize(selectedFile.size, formatNumber)})</p> : null}
      {actionError ? <p className="mt-3 text-sm text-rose-700 dark:text-rose-200" role="alert"><T>{actionError}</T></p> : null}

      <div className="mt-5">
        {isLoading ? <LoadingState label="Loading attachments..." /> : null}
        {!isLoading && error ? <ErrorState action={<Button onClick={reload}><T>Try again</T></Button>} description={error} title="Unable to load attachments" /> : null}
        {!isLoading && !error && items.length === 0 ? <EmptyState description="Upload a file when this record needs supporting context." title="No attachments yet" /> : null}
        {!isLoading && !error && items.length > 0 ? <ul className="divide-y divide-slate-100 overflow-hidden rounded-xl border border-slate-200 dark:divide-slate-800 dark:border-slate-800">{items.map((attachment) => <li className="flex flex-col gap-3 p-4 sm:flex-row sm:items-center sm:justify-between" key={attachment.id}><div className="min-w-0"><a className="block truncate text-sm font-semibold text-indigo-600 hover:text-indigo-500 dark:text-indigo-300" href={attachmentService.downloadPath(attachment.id)}>{attachment.original_filename}</a><p className="mt-1 text-xs text-slate-500">{formatFileSize(attachment.size_bytes, formatNumber)} · {attachment.content_type} · <LocalizedDateTime value={attachment.created_at} /></p></div><Button disabled={isDeletingId === attachment.id} onClick={() => void deleteAttachment(attachment.id, attachment.original_filename)} size="sm" variant="danger">{isDeletingId === attachment.id ? <T>Deleting...</T> : <T>Delete</T>}</Button></li>)}</ul> : null}
        {!error ? <PaginationControls isLoading={isLoading} meta={meta} onPageChange={setPage} /> : null}
      </div>
    </section>
  );
}
