import React, { useState } from 'react';
import { Button } from '../common/Button';
import { 
  X, 
  Table, 
  FileSpreadsheet, 
  Check, 
  Download, 
  FolderOpen, 
  AlertTriangle, 
  CheckCircle2,
  Loader2
} from 'lucide-react';

interface ExportModalProps {
  isOpen: boolean;
  onClose: () => void;
  exceptionsCount: number;
  totalRecordsCount: number;
}

export const ExportModal: React.FC<ExportModalProps> = ({
  isOpen,
  onClose,
  exceptionsCount,
  totalRecordsCount,
}) => {
  const [scope, setScope] = useState<'exceptions' | 'all'>('exceptions');
  const [fileName, setFileName] = useState('Reconciliation_Report_2024-09-15.xlsx');
  const [destPath, setDestPath] = useState('C:\\Users\\Analyst\\Documents\\Reconcile\\');
  const [isExporting, setIsExporting] = useState(false);
  const [isDone, setIsDone] = useState(false);

  if (!isOpen) return null;

  const handleExport = () => {
    setIsExporting(true);
    setTimeout(() => {
      setIsExporting(false);
      setIsDone(true);
      setTimeout(() => {
        setIsDone(false);
        onClose();
      }, 1500);
    }, 1200);
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/40 backdrop-blur-2xs select-none">
      <div className="bg-white rounded-xl border border-outline-variant/80 shadow-2xl w-full max-w-lg overflow-hidden animate-in fade-in zoom-in-95 duration-150">
        {/* Modal Header */}
        <div className="flex items-center justify-between p-5 border-b border-gray-100">
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 rounded-lg bg-surface-low text-secondary flex items-center justify-center shrink-0 border border-secondary/20">
              <FileSpreadsheet className="w-5 h-5" />
            </div>
            <div>
              <h2 className="text-sm font-bold text-on-surface">Export reconciliation report</h2>
              <p className="text-xs text-on-surface-variant">
                Generate an Excel spreadsheet with your results.
              </p>
            </div>
          </div>

          <button
            type="button"
            onClick={onClose}
            className="w-7 h-7 rounded flex items-center justify-center text-gray-400 hover:text-gray-700 hover:bg-gray-100 transition-colors cursor-pointer"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* Modal Body */}
        <div className="p-5 space-y-4 text-xs">
          {/* Readiness Info Pill */}
          <div className="flex items-center justify-between p-2.5 rounded bg-surface-low text-secondary border border-secondary/15 font-medium">
            <span className="flex items-center gap-1.5">
              <CheckCircle2 className="w-4 h-4 text-emerald-600" />
              <span className="text-on-surface">Ready to export • {totalRecordsCount.toLocaleString()} records processed</span>
            </span>
            <span className="font-mono text-[11px] text-gray-500">~1.1 MB</span>
          </div>

          {/* Export Scope Toggle */}
          <div>
            <label className="text-[11px] font-semibold text-on-surface-variant uppercase tracking-wider block mb-2">
              Export Scope
            </label>
            <div className="grid grid-cols-2 gap-3">
              {/* Exceptions only card */}
              <div
                onClick={() => setScope('exceptions')}
                className={`p-3 rounded-lg border text-left cursor-pointer transition-all ${
                  scope === 'exceptions'
                    ? 'bg-surface-low border-secondary shadow-xs ring-1 ring-secondary'
                    : 'bg-white border-outline-variant/60 hover:bg-gray-50'
                }`}
              >
                <div className="flex items-center justify-between mb-1">
                  <span className="flex items-center gap-1.5 font-bold text-on-surface">
                    <AlertTriangle className="w-3.5 h-3.5 text-amber-600" />
                    <span>Exceptions only</span>
                  </span>
                  <span className={`w-3.5 h-3.5 rounded-full flex items-center justify-center text-[9px] text-white ${
                    scope === 'exceptions' ? 'bg-secondary' : 'border border-gray-300'
                  }`}>
                    {scope === 'exceptions' && '✓'}
                  </span>
                </div>
                <p className="text-[11px] text-on-surface-variant mt-1 leading-snug">
                  Exports <strong className="font-mono">{exceptionsCount}</strong> flagged discrepancy rows for quick review.
                </p>
              </div>

              {/* All records card */}
              <div
                onClick={() => setScope('all')}
                className={`p-3 rounded-lg border text-left cursor-pointer transition-all ${
                  scope === 'all'
                    ? 'bg-surface-low border-secondary shadow-xs ring-1 ring-secondary'
                    : 'bg-white border-outline-variant/60 hover:bg-gray-50'
                }`}
              >
                <div className="flex items-center justify-between mb-1">
                  <span className="flex items-center gap-1.5 font-bold text-on-surface">
                    <Table className="w-3.5 h-3.5 text-secondary" />
                    <span>All records</span>
                  </span>
                  <span className={`w-3.5 h-3.5 rounded-full flex items-center justify-center text-[9px] text-white ${
                    scope === 'all' ? 'bg-secondary' : 'border border-gray-300'
                  }`}>
                    {scope === 'all' && '✓'}
                  </span>
                </div>
                <p className="text-[11px] text-on-surface-variant mt-1 leading-snug">
                  Exports all <strong className="font-mono">{totalRecordsCount.toLocaleString()}</strong> rows (matched + exceptions).
                </p>
              </div>
            </div>
          </div>

          {/* Included Sheets Checklist */}
          <div>
            <label className="text-[11px] font-semibold text-on-surface-variant uppercase tracking-wider block mb-2">
              Included in this workbook
            </label>
            <div className="space-y-1.5 bg-gray-50 p-3 rounded-lg border border-gray-100">
              <div className="flex items-center gap-2 text-on-surface">
                <Check className="w-3.5 h-3.5 text-secondary" />
                <span>Summary sheet with totals and status breakdown</span>
              </div>
              <div className="flex items-center gap-2 text-on-surface">
                <Check className="w-3.5 h-3.5 text-secondary" />
                <span>Exceptions & variance deltas worksheet</span>
              </div>
              <div className="flex items-center gap-2 text-on-surface">
                <Check className="w-3.5 h-3.5 text-secondary" />
                <span>All records master sheet</span>
              </div>
              <div className="flex items-center gap-2 text-on-surface">
                <Check className="w-3.5 h-3.5 text-secondary" />
                <span>Entity grouping breakdown sheet</span>
              </div>
            </div>
          </div>

          {/* Destination Path & File Name */}
          <div className="space-y-2">
            <div>
              <label className="text-[11px] font-medium text-on-surface-variant block mb-1">
                File Name
              </label>
              <input
                type="text"
                value={fileName}
                onChange={(e) => setFileName(e.target.value)}
                className="w-full h-8 px-2.5 text-xs font-mono bg-gray-50 border border-outline-variant/60 rounded text-on-surface outline-none focus:border-secondary focus:bg-white"
              />
            </div>

            <div>
              <label className="text-[11px] font-medium text-on-surface-variant block mb-1">
                Destination Folder
              </label>
              <div className="flex items-center gap-2">
                <input
                  type="text"
                  value={destPath}
                  onChange={(e) => setDestPath(e.target.value)}
                  className="flex-1 h-8 px-2.5 rounded bg-gray-50 border border-outline-variant/60 text-xs font-mono text-gray-700 truncate outline-none focus:border-secondary focus:bg-white"
                />
                <Button variant="secondary" size="sm" icon={<FolderOpen className="w-3.5 h-3.5" />}>
                  Browse...
                </Button>
              </div>
            </div>
          </div>
        </div>

        {/* Modal Footer Actions */}
        <div className="flex items-center justify-between p-4 bg-gray-50/80 border-t border-gray-100">
          <Button variant="ghost" size="sm" onClick={onClose} disabled={isExporting}>
            Cancel
          </Button>

          <Button
            variant="primary"
            size="md"
            onClick={handleExport}
            disabled={isExporting || isDone}
            icon={
              isExporting ? (
                <Loader2 className="w-4 h-4 animate-spin" />
              ) : isDone ? (
                <Check className="w-4 h-4 text-white" />
              ) : (
                <Download className="w-4 h-4" />
              )
            }
          >
            {isExporting ? 'Writing .xlsx...' : isDone ? 'Export Complete!' : 'Export Excel (.xlsx)'}
          </Button>
        </div>
      </div>
    </div>
  );
};
