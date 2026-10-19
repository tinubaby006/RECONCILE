import React, { useState } from 'react';
import type { 
  DatasetMeta, 
  ColumnMapping, 
  ReconciliationRecord, 
  WorkflowStep 
} from './types/reconcile';
import { 
  mockDatasetA, 
  mockDatasetB, 
  mockMappings, 
  mockRecords, 
  mockSummary 
} from './data/mockData';
import { Header } from './components/common/Header';
import { ImportScreen } from './components/screens/ImportScreen';
import { MappingScreen } from './components/screens/MappingScreen';
import { ResultsScreen } from './components/screens/ResultsScreen';
import { RecordDetailScreen } from './components/screens/RecordDetailScreen';
import { ExportModal } from './components/screens/ExportModal';

export const App: React.FC = () => {
  // Workflow Navigation State
  const [currentStep, setCurrentStep] = useState<WorkflowStep>('import');

  // Datasets State (Initialized with prototype sample datasets for immediate exploration)
  const [datasetA, setDatasetA] = useState<DatasetMeta | null>(mockDatasetA);
  const [datasetB, setDatasetB] = useState<DatasetMeta | null>(mockDatasetB);

  // Mappings State
  const [mappings, setMappings] = useState<ColumnMapping[]>(mockMappings);

  // Records & Summary State
  const [records, setRecords] = useState<ReconciliationRecord[]>(mockRecords);
  const [summary, setSummary] = useState(mockSummary);

  // Record Detail Active Selection
  const [selectedRecordId, setSelectedRecordId] = useState<string>('rec-8841');

  // Export Modal Toggle
  const [isExportOpen, setIsExportOpen] = useState(false);

  // Reset / Load Sample Data
  const handleLoadSampleData = () => {
    setDatasetA(mockDatasetA);
    setDatasetB(mockDatasetB);
    setMappings(mockMappings);
    setRecords(mockRecords);
    setSummary(mockSummary);
    setSelectedRecordId('rec-8841');
    setCurrentStep('import');
  };

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

  // Record Override Actions
  const handleConfirmMatch = (recordId: string) => {
    setRecords((prev) =>
      prev.map((r) => {
        if (r.id === recordId) {
          return {
            ...r,
            status: 'matched',
            status_label: 'Confirmed Match',
            user_override: 'confirmed',
          };
        }
        return r;
      })
    );
  };

  const handleMarkUnmatched = (recordId: string) => {
    setRecords((prev) =>
      prev.map((r) => {
        if (r.id === recordId) {
          return {
            ...r,
            status: 'missing_in_b',
            status_label: 'Marked Unmatched',
            record_b: null,
            source_b: null,
            amount_b: null,
            amount_diff: r.amount_a ? -r.amount_a : null,
            user_override: 'unmatched',
          };
        }
        return r;
      })
    );
  };

  const handleSwitchCandidate = (recordId: string, candidateId: string) => {
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
  };

  return (
    <div className="min-h-screen bg-canvas text-on-surface flex flex-col font-sans select-none antialiased">
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
            onContinue={() => setCurrentStep('mapping')}
            onLoadSampleData={handleLoadSampleData}
          />
        )}

        {currentStep === 'mapping' && datasetA && datasetB && (
          <MappingScreen
            datasetA={datasetA}
            datasetB={datasetB}
            mappings={mappings}
            onUpdateMapping={handleUpdateMapping}
            onBack={() => setCurrentStep('import')}
            onReconcile={() => setCurrentStep('results')}
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

      {/* Screen 5: Excel Export Modal Dialog */}
      <ExportModal
        isOpen={isExportOpen}
        onClose={() => setIsExportOpen(false)}
        exceptionsCount={records.filter((r) => r.status !== 'matched').length}
        totalRecordsCount={records.length}
      />
    </div>
  );
};

export default App;
