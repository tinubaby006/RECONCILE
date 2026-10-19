import { invoke } from '@tauri-apps/api/core';
import { listen } from '@tauri-apps/api/event';
import type { 
  DatasetMeta, 
  ColumnMapping, 
  ReconciliationSummary, 
  ReconciliationRecord 
} from '../types/reconcile';

export function isTauriEnvironment(): boolean {
  return typeof window !== 'undefined' && '__TAURI_INTERNALS__' in window;
}

export async function pickFile(title?: string, defaultPath?: string): Promise<string | null> {
  if (!isTauriEnvironment()) {
    console.warn('[tauriClient] Not running in Tauri environment.');
    return null;
  }
  return await invoke<string | null>('pick_file', { title, defaultPath });
}

export async function inspectFile(filePath: string, sheetName?: string): Promise<DatasetMeta> {
  if (!isTauriEnvironment()) {
    throw new Error('Tauri environment required to inspect local files.');
  }
  return await invoke<DatasetMeta>('inspect_file', { 
    filePath, 
    sheetName: sheetName || null 
  });
}

export async function mapColumns(
  fileA: string, 
  fileB: string, 
  sheetA?: string, 
  sheetB?: string
): Promise<{ meta_a: DatasetMeta; meta_b: DatasetMeta; mappings: ColumnMapping[] }> {
  if (!isTauriEnvironment()) {
    throw new Error('Tauri environment required to map columns.');
  }
  return await invoke<{ meta_a: DatasetMeta; meta_b: DatasetMeta; mappings: ColumnMapping[] }>(
    'map_columns',
    {
      fileA,
      fileB,
      sheetA: sheetA || null,
      sheetB: sheetB || null,
    }
  );
}

export interface ReconcilePayload {
  file_a: string;
  file_b: string;
  sheet_a?: string | null;
  sheet_b?: string | null;
  mappings: ColumnMapping[];
  overrides?: Record<string, unknown>;
  rules?: Record<string, unknown>;
}

export interface ReconcileResult {
  summary: ReconciliationSummary;
  records: ReconciliationRecord[];
  entities: Record<string, ReconciliationRecord[]>;
}

export async function runReconciliation(payload: ReconcilePayload): Promise<ReconcileResult> {
  if (!isTauriEnvironment()) {
    throw new Error('Tauri environment required to run reconciliation.');
  }
  return await invoke<ReconcileResult>('run_reconciliation', { payload });
}

export interface ProgressEventPayload {
  type: string;
  percent: number;
  message: string;
}

export async function listenEngineProgress(
  callback: (progress: ProgressEventPayload) => void
): Promise<() => void> {
  if (!isTauriEnvironment()) {
    return () => {};
  }
  const unlisten = await listen<ProgressEventPayload>('engine-progress', (event) => {
    callback(event.payload);
  });
  return unlisten;
}
