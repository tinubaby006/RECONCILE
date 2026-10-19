import React, { useState } from 'react';
import type { DatasetMeta } from '../../types/reconcile';
import { Button } from '../common/Button';
import { Badge } from '../common/Badge';
import { 
  FileSpreadsheet, 
  UploadCloud, 
  FileText, 
  ArrowRight, 
  RotateCcw, 
  CheckCircle2, 
  Layers, 
  AlertCircle 
} from 'lucide-react';

interface ImportScreenProps {
  datasetA: DatasetMeta | null;
  datasetB: DatasetMeta | null;
  onSetDatasetA: (meta: DatasetMeta | null) => void;
  onSetDatasetB: (meta: DatasetMeta | null) => void;
  onContinue: () => void;
  onLoadSampleData: () => void;
}

export const ImportScreen: React.FC<ImportScreenProps> = ({
  datasetA,
  datasetB,
  onSetDatasetA,
  onSetDatasetB,
  onContinue,
  onLoadSampleData,
}) => {
  const [selectedSheetA, setSelectedSheetA] = useState<string>(
    datasetA?.active_sheet || (datasetA?.sheets[0] ?? '')
  );

  const canContinue = Boolean(datasetA && datasetB);

  return (
    <div className="flex-1 flex flex-col p-6 max-w-5xl mx-auto w-full">
      {/* Title & Description */}
      <div className="flex items-center justify-between pb-6 border-b border-outline-variant/40">
        <div>
          <h1 className="text-xl font-bold tracking-tight text-on-surface">New reconciliation</h1>
          <p className="text-xs text-on-surface-variant mt-1">
            Import two datasets to automatically detect matching columns, compare records, and review discrepancies.
          </p>
        </div>
        <Button
          variant="secondary"
          size="sm"
          onClick={onLoadSampleData}
          icon={<RotateCcw className="w-3.5 h-3.5 text-secondary" />}
        >
          Load Realistic Sample Data
        </Button>
      </div>

      {/* Side-by-Side Dataset Import Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mt-6">
        {/* Dataset A Card */}
        <div className="bg-white rounded-lg border border-outline-variant/60 shadow-xs p-5 flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between pb-3 border-b border-outline-variant/30">
              <div>
                <h2 className="text-sm font-bold text-primary">Dataset A (First file)</h2>
                <span className="text-xs text-on-surface-variant">Source or baseline ledger</span>
              </div>
              {datasetA ? (
                <Badge status="ready" label="File ready" />
              ) : (
                <span className="text-xs text-gray-400 font-medium">Pending selection</span>
              )}
            </div>

            {datasetA ? (
              <div className="mt-4 space-y-4">
                <div className="flex items-center justify-between bg-surface-low p-3.5 rounded border border-secondary/15">
                  <div className="flex items-center gap-3 min-w-0">
                    <div className="w-10 h-10 rounded bg-white flex items-center justify-center text-primary shrink-0 shadow-2xs border border-outline-variant/30">
                      <FileSpreadsheet className="w-5 h-5 text-secondary" />
                    </div>
                    <div className="min-w-0">
                      <div className="text-xs font-semibold text-on-surface truncate">
                        {datasetA.file_name}
                      </div>
                      <div className="text-[11px] text-on-surface-variant mt-0.5">
                        {datasetA.file_type.toUpperCase()} file • {datasetA.file_size || '1.8 MB'} •{' '}
                        <span className="font-mono">{datasetA.total_rows.toLocaleString()}</span> rows
                      </div>
                    </div>
                  </div>
                  <button
                    type="button"
                    onClick={() => onSetDatasetA(null)}
                    className="text-xs text-secondary hover:underline font-medium ml-2 cursor-pointer"
                  >
                    Change file
                  </button>
                </div>

                {datasetA.sheets && datasetA.sheets.length > 0 && (
                  <div className="flex items-center justify-between bg-gray-50 p-2.5 rounded border border-outline-variant/30 text-xs">
                    <div className="flex items-center gap-1.5 text-on-surface-variant">
                      <Layers className="w-3.5 h-3.5" />
                      <span>Select Worksheet:</span>
                    </div>
                    <select
                      value={selectedSheetA}
                      onChange={(e) => setSelectedSheetA(e.target.value)}
                      className="bg-white border border-outline-variant/60 rounded px-2 py-1 text-xs text-on-surface outline-none cursor-pointer focus:border-secondary"
                    >
                      {datasetA.sheets.map((sheet) => (
                        <option key={sheet} value={sheet}>
                          {sheet}
                        </option>
                      ))}
                    </select>
                  </div>
                )}
              </div>
            ) : (
              <div className="mt-4 border-2 border-dashed border-outline-variant/60 rounded-lg p-8 flex flex-col items-center justify-center text-center hover:bg-surface-low/50 transition-colors cursor-pointer">
                <UploadCloud className="w-8 h-8 text-secondary/60 mb-2" />
                <span className="text-xs font-semibold text-on-surface">Click to select Dataset A</span>
                <span className="text-[11px] text-on-surface-variant mt-1">Supports CSV, XLSX, or JSON</span>
                <div className="flex gap-1.5 mt-3">
                  <span className="px-1.5 py-0.5 rounded bg-gray-100 text-[10px] text-gray-600 font-mono">.csv</span>
                  <span className="px-1.5 py-0.5 rounded bg-gray-100 text-[10px] text-gray-600 font-mono">.xlsx</span>
                  <span className="px-1.5 py-0.5 rounded bg-gray-100 text-[10px] text-gray-600 font-mono">.json</span>
                </div>
              </div>
            )}
          </div>

          <div className="mt-4 pt-3 border-t border-outline-variant/20 flex items-center justify-between text-[11px] text-on-surface-variant">
            <span>Primary reference data</span>
            <span className="text-emerald-700 flex items-center gap-1 font-medium">
              <CheckCircle2 className="w-3 h-3" /> Read-only mode
            </span>
          </div>
        </div>

        {/* Dataset B Card */}
        <div className="bg-white rounded-lg border border-outline-variant/60 shadow-xs p-5 flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between pb-3 border-b border-outline-variant/30">
              <div>
                <h2 className="text-sm font-bold text-secondary">Dataset B (Second file)</h2>
                <span className="text-xs text-on-surface-variant">Comparison file or bank statement</span>
              </div>
              {datasetB ? (
                <Badge status="ready" label="File ready" />
              ) : (
                <span className="text-xs text-gray-400 font-medium">Pending selection</span>
              )}
            </div>

            {datasetB ? (
              <div className="mt-4 space-y-4">
                <div className="flex items-center justify-between bg-surface-low p-3.5 rounded border border-secondary/15">
                  <div className="flex items-center gap-3 min-w-0">
                    <div className="w-10 h-10 rounded bg-white flex items-center justify-center text-secondary shrink-0 shadow-2xs border border-outline-variant/30">
                      <FileText className="w-5 h-5 text-secondary" />
                    </div>
                    <div className="min-w-0">
                      <div className="text-xs font-semibold text-on-surface truncate">
                        {datasetB.file_name}
                      </div>
                      <div className="text-[11px] text-on-surface-variant mt-0.5">
                        {datasetB.file_type.toUpperCase()} file • {datasetB.file_size || '1.4 MB'} •{' '}
                        <span className="font-mono">{datasetB.total_rows.toLocaleString()}</span> rows
                      </div>
                    </div>
                  </div>
                  <button
                    type="button"
                    onClick={() => onSetDatasetB(null)}
                    className="text-xs text-secondary hover:underline font-medium ml-2 cursor-pointer"
                  >
                    Change file
                  </button>
                </div>
              </div>
            ) : (
              <div className="mt-4 border-2 border-dashed border-outline-variant/60 rounded-lg p-8 flex flex-col items-center justify-center text-center hover:bg-surface-low/50 transition-colors cursor-pointer">
                <UploadCloud className="w-8 h-8 text-secondary/60 mb-2" />
                <span className="text-xs font-semibold text-on-surface">Click to select Dataset B</span>
                <span className="text-[11px] text-on-surface-variant mt-1">Supports CSV, XLSX, or JSON</span>
                <div className="flex gap-1.5 mt-3">
                  <span className="px-1.5 py-0.5 rounded bg-gray-100 text-[10px] text-gray-600 font-mono">.csv</span>
                  <span className="px-1.5 py-0.5 rounded bg-gray-100 text-[10px] text-gray-600 font-mono">.xlsx</span>
                  <span className="px-1.5 py-0.5 rounded bg-gray-100 text-[10px] text-gray-600 font-mono">.json</span>
                </div>
              </div>
            )}
          </div>

          <div className="mt-4 pt-3 border-t border-outline-variant/20 flex items-center justify-between text-[11px] text-on-surface-variant">
            <span>Counterpart reconciliation file</span>
            <span className="text-emerald-700 flex items-center gap-1 font-medium">
              <CheckCircle2 className="w-3 h-3" /> Read-only mode
            </span>
          </div>
        </div>
      </div>

      {/* Validation Banner if missing files */}
      {!canContinue && (
        <div className="mt-6 flex items-center gap-2 p-3 bg-amber-50 text-amber-800 border border-amber-200 rounded text-xs">
          <AlertCircle className="w-4 h-4 shrink-0" />
          <span>Both Dataset A and Dataset B must be loaded to continue to column mapping.</span>
        </div>
      )}

      {/* Footer Navigation Bar */}
      <div className="mt-8 pt-4 border-t border-outline-variant/40 flex items-center justify-between">
        <Button
          variant="ghost"
          size="sm"
          onClick={() => {
            onSetDatasetA(null);
            onSetDatasetB(null);
          }}
          disabled={!datasetA && !datasetB}
        >
          Clear files
        </Button>

        <Button
          variant="primary"
          size="md"
          onClick={onContinue}
          disabled={!canContinue}
          icon={<ArrowRight className="w-4 h-4" />}
        >
          Continue to column mapping
        </Button>
      </div>
    </div>
  );
};
