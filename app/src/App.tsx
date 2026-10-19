import React, { useState, useEffect, useCallback } from 'react';
import type { 
  DatasetMeta, 
  ColumnMapping, 
  ReconciliationRecord, 
  ReconciliationSummary,
  WorkflowStep 
} from './types/reconcile';
import { 
  mockDatasetA, 
  mockDatasetB, 
  mockMappings, 
  mockRecords, 
  mockSummary 
} from './data/mockData';
import { 
  pickFile, 
  inspectFile, 
  mapColumns, 
  runReconciliation, 
  listenEngineProgress 
} from './services/tauriClient';
import { Header } from './components/common/Header';
import { ImportScreen } from './components/screens/ImportScreen';
import { MappingScreen } from './components/screens/MappingScreen';
import { ResultsScreen } from './components/screens/ResultsScreen';
import { RecordDetailScreen } from './components/screens/RecordDetailScreen';
import { ExportModal } from './components/screens/ExportModal';
import { Loader2 } from 'lucide-react';

export const App: React.FC = () => {
  // Workflow Navigation State
  const [currentStep, setCurrentStep] = useState<WorkflowStep>('import');

  // Datasets State
  const [isRealRun, setIsRealRun] = useState(false);
  const [datasetA, setDatasetA] = useState<DatasetMeta | null>(mockDatasetA);
  const [datasetB, setDatasetB] = useState<DatasetMeta | null>(mockDatasetB);

  // Mappings State
  const [mappings, setMappings] = useState<ColumnMapping[]>(mockMappings);

  // Records & Summary State
  const [records, setRecords] = useState<ReconciliationRecord[]>(mockRecords);
  const [summary, setSummary] = useState<ReconciliationSummary>(mockSummary);

  // Overrides State (persisted across re-runs)
  const [userOverrides, setUserOverrides] = useState<Record<string, { action: string; candidate_id?: string }>>({});

  // Record Detail Active Selection
  const [selectedRecordId, setSelectedRecordId] = useState<string>('rec-8841');

  // Status & Progress States
  const [isLoadingA, setIsLoadingA] = useState(false);
  const [isLoadingB, setIsLoadingB] = useState(false);
  const [isProcessing, setIsProcessing] = useState(false);
  const [progressMessage, setProgressMessage] = useState('');
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  // Export Modal Toggle
  const [isExportOpen, setIsExportOpen] = useState(false);

  // Subscribe to real-time engine progress events via NDJSON/Tauri events
  useEffect(() => {
    let unlistenFn: (() => void) | null = null;
    listenEngineProgress((progress) => {
      setProgressMessage(`${progress.message} (${progress.percent}%)`);
    }).then((unlisten) => {
      unlistenFn = unlisten;
    });

    return () => {
      if (unlistenFn) unlistenFn();
    };
  }, []);

  // Load Sample Realistic Mock Data
  const handleLoadSampleData = () => {
    setIsRealRun(false);
    setUserOverrides({});
    setDatasetA(mockDatasetA);
    setDatasetB(mockDatasetB);
    setMappings(mockMappings);
    setRecords(mockRecords);
    setSummary(mockSummary);
    setSelectedRecordId('rec-8841');
    setCurrentStep('import');
    setErrorMessage(null);
  };

  // Inspect file helper
  const handleInspectPathA = async (filePath: string, sheetName?: string) => {
    if (!filePath) return;
    setIsLoadingA(true);
    setErrorMessage(null);
    try {
      const meta = await inspectFile(filePath, sheetName);
      setDatasetA(meta);
      setIsRealRun(true);
      setUserOverrides({});
    } catch (err: unknown) {
      setErrorMessage(`Failed to load Dataset A: ${err instanceof Error ? err.message : String(err)}`);
    } finally {
      setIsLoadingA(false);
    }
  };

  const handleInspectPathB = async (filePath: string, sheetName?: string) => {
    if (!filePath) return;
    setIsLoadingB(true);
    setErrorMessage(null);
    try {
      const meta = await inspectFile(filePath, sheetName);
      setDatasetB(meta);
      setIsRealRun(true);
      setUserOverrides({});
    } catch (err: unknown) {
      setErrorMessage(`Failed to load Dataset B: ${err instanceof Error ? err.message : String(err)}`);
    } finally {
      setIsLoadingB(false);
    }
  };

  // Pick file through native dialog
  const handlePickFileA = async () => {
    try {
      const selected = await pickFile('Select Dataset A (Source / Ledger)');
      if (selected) {
        await handleInspectPathA(selected);
      }
    } catch (err: unknown) {
      setErrorMessage(`Error picking file for Dataset A: ${err instanceof Error ? err.message : String(err)}`);
    }
  };

  const handlePickFileB = async () => {
    try {
      const selected = await pickFile('Select Dataset B (Comparison / Statement)');
      if (selected) {
        await handleInspectPathB(selected);
      }
    } catch (err: unknown) {
      setErrorMessage(`Error picking file for Dataset B: ${err instanceof Error ? err.message : String(err)}`);
    }
  };

  // Proceed to Column Mapping Screen
  const handleContinueToMapping = async () => {
    if (!datasetA || !datasetB) return;

    if (!isRealRun) {
      // Prototype mock mode
      setCurrentStep('mapping');
      return;
    }

    setIsProcessing(true);
    setProgressMessage('Analyzing dataset columns...');
    setErrorMessage(null);

    try {
      const result = await mapColumns(
        datasetA.file_path,
        datasetB.file_path,
        datasetA.active_sheet || undefined,
        datasetB.active_sheet || undefined
      );
      setMappings(result.mappings);
      setCurrentStep('mapping');
    } catch (err: unknown) {
      setErrorMessage(`Failed to map columns: ${err instanceof Error ? err.message : String(err)}`);
    } finally {
      setIsProcessing(false);
    }
  };

  // Execute Reconcile via Engine
  const executeReconcile = useCallback(async (overridesToApply = userOverrides) => {
    if (!datasetA || !datasetB) return;

    if (!isRealRun) {
      // In mock mode, just switch to results
      setCurrentStep('results');
      return;
    }

    setIsProcessing(true);
    setProgressMessage('Running reconciliation engine...');
    setErrorMessage(null);

    try {
      const result = await runReconciliation({
        file_a: datasetA.file_path,
        file_b: datasetB.file_path,
        sheet_a: datasetA.active_sheet || null,
        sheet_b: datasetB.active_sheet || null,
        mappings,
        overrides: overridesToApply,
        rules: {
          amount_tolerance: 0.01,
          date_tolerance_days: 7,
          entity_similarity_threshold: 70.0,
        },
      });

      setSummary(result.summary);
      setRecords(result.records);
      if (result.records.length > 0) {
        setSelectedRecordId(result.records[0].id);
      }
      setCurrentStep('results');
    } catch (err: unknown) {
      setErrorMessage(`Reconciliation failed: ${err instanceof Error ? err.message : String(err)}`);
    } finally {
      setIsProcessing(false);
    }
  }, [datasetA, datasetB, isRealRun, mappings, userOverrides]);

  // Update specific column mapping
  const handleUpdateMapping = (index: number, updated: Partial<ColumnMapping>) => {
    setMappings((prev) => {
      const next = [...prev];
      next[index] = { ...next[index], ...updated };
      return next;
    });
  };

  // Handle Record Detail Navigation
  const selectedRecord = records.find((r) => r.id === selectedRecordId) || records[0];
  const recordIndex = records.findIndex((r) => r.id === selectedRecordId);

  const handlePrevRecord = () => {
    if (recordIndex > 0) {
      setSelectedRecordId(records[recordIndex - 1].id);
    }
  };

  const handleNextRecord = () => {
    if (recordIndex < records.length - 1) {
      setSelectedRecordId(records[recordIndex + 1].id);
    }
  };

  // Record Override Actions (Refreshed through engine when in real mode)
  const handleConfirmMatch = async (recordId: string) => {
    const nextOverrides = {
      ...userOverrides,
      [recordId]: { action: 'confirm' },
    };
    setUserOverrides(nextOverrides);

    if (isRealRun) {
      await executeReconcile(nextOverrides);
    } else {
      // Mock mode optimistic update
      setRecords((prev) =>
        prev.map((r) =>
          r.id === recordId
            ? { ...r, status: 'matched', status_label: 'Confirmed Match', user_override: 'confirmed' }
            : r
        )
      );
    }
  };

  const handleMarkUnmatched = async (recordId: string) => {
    const nextOverrides = {
      ...userOverrides,
      [recordId]: { action: 'unmatched' },
    };
    setUserOverrides(nextOverrides);

    if (isRealRun) {
      await executeReconcile(nextOverrides);
    } else {
      // Mock mode optimistic update
      setRecords((prev) =>
        prev.map((r) =>
          r.id === recordId
            ? {
                ...r,
                status: 'missing_in_b',
                status_label: 'Marked Unmatched',
                record_b: null,
                source_b: null,
                amount_b: null,
                amount_diff: r.amount_a ? -r.amount_a : null,
                user_override: 'unmatched',
              }
            : r
        )
      );
    }
  };

  const handleSwitchCandidate = async (recordId: string, candidateId: string) => {
    const nextOverrides = {
      ...userOverrides,
      [recordId]: { action: 'switch_candidate', candidate_id: candidateId },
    };
    setUserOverrides(nextOverrides);

    if (isRealRun) {
      await executeReconcile(nextOverrides);
    } else {
      // Mock mode optimistic update
      setRecords((prev) =>
        prev.map((r) => {
          if (r.id === recordId) {
            const cand = r.candidates.find((c) => c.candidate_id === candidateId);
            if (cand) {
              return {
                ...r,
                record_b: cand.record_b,
                source_b: cand.source_b,
                amount_b: cand.amount_b,
                date_b: cand.date_b,
                amount_diff:
                  r.amount_a !== null && r.amount_a !== undefined && cand.amount_b !== null && cand.amount_b !== undefined
                    ? Math.round((cand.amount_b - r.amount_a) * 100) / 100
                    : null,
                status: 'matched',
                status_label: 'Confirmed Match',
                user_override: 'switched_candidate',
              };
            }
          }
          return r;
        })
      );
    }
  };

  return (
    <div className="min-h-screen bg-canvas text-on-surface flex flex-col font-sans select-none antialiased relative">
      {/* Top Application Bar */}
      <Header
        currentStep={currentStep}
        onNavigate={(step) => setCurrentStep(step)}
        hasFiles={Boolean(datasetA && datasetB)}
        hasResults={records.length > 0}
        onOpenExport={() => setIsExportOpen(true)}
      />

      {/* Main Workflow View Routing */}
      <main className="flex-1 flex flex-col overflow-y-auto">
        {currentStep === 'import' && (
          <ImportScreen
            datasetA={datasetA}
            datasetB={datasetB}
            onSetDatasetA={setDatasetA}
            onSetDatasetB={setDatasetB}
            onPickFileA={handlePickFileA}
            onPickFileB={handlePickFileB}
            onInspectPathA={handleInspectPathA}
            onInspectPathB={handleInspectPathB}
            onContinue={handleContinueToMapping}
            onLoadSampleData={handleLoadSampleData}
            isLoadingA={isLoadingA}
            isLoadingB={isLoadingB}
            errorMessage={errorMessage}
            onClearError={() => setErrorMessage(null)}
          />
        )}

        {currentStep === 'mapping' && datasetA && datasetB && (
          <MappingScreen
            datasetA={datasetA}
            datasetB={datasetB}
            mappings={mappings}
            onUpdateMapping={handleUpdateMapping}
            onBack={() => setCurrentStep('import')}
            onReconcile={() => executeReconcile()}
            isLoading={isProcessing}
            progressMessage={progressMessage}
          />
        )}

        {currentStep === 'results' && (
          <ResultsScreen
            summary={summary}
            records={records}
            onSelectRecord={(rec) => {
              setSelectedRecordId(rec.id);
              setCurrentStep('detail');
            }}
            onOpenExport={() => setIsExportOpen(true)}
          />
        )}

        {currentStep === 'detail' && selectedRecord && (
          <RecordDetailScreen
            record={selectedRecord}
            recordIndex={recordIndex >= 0 ? recordIndex : 0}
            totalRecords={records.length}
            onBack={() => setCurrentStep('results')}
            onPrevRecord={handlePrevRecord}
            onNextRecord={handleNextRecord}
            onConfirmMatch={handleConfirmMatch}
            onMarkUnmatched={handleMarkUnmatched}
            onSwitchCandidate={handleSwitchCandidate}
          />
        )}
      </main>

      {/* Global Processing Overlay */}
      {isProcessing && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/40 backdrop-blur-2xs">
          <div className="bg-white rounded-xl border border-outline-variant/80 shadow-2xl p-6 flex flex-col items-center max-w-sm w-full text-center">
            <Loader2 className="w-9 h-9 text-secondary animate-spin mb-3" />
            <h3 className="text-sm font-bold text-on-surface">Processing Datasets</h3>
            <p className="text-xs text-on-surface-variant mt-1 font-mono">
              {progressMessage || 'Communicating with local Python engine...'}
            </p>
          </div>
        </div>
      )}

      {/* Screen 5: Excel Export Modal Dialog */}
      <ExportModal
        isOpen={isExportOpen}
        onClose={() => setIsExportOpen(false)}
        summary={summary}
        records={records}
        datasetA={datasetA}
        datasetB={datasetB}
        exceptionsCount={records.filter((r) => r.status !== 'matched').length}
        totalRecordsCount={records.length}
      />
    </div>
  );
};

export default App;
