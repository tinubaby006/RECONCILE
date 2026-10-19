import type { WorkflowStep } from '../../types/reconcile';
import { ShieldCheck, FileSpreadsheet, GitCompare, TableProperties, Download } from 'lucide-react';

interface HeaderProps {
  currentStep: WorkflowStep;
  onNavigate: (step: WorkflowStep) => void;
  hasFiles: boolean;
  hasResults: boolean;
  onOpenExport?: () => void;
}

export const Header: React.FC<HeaderProps> = ({
  currentStep,
  onNavigate,
  hasFiles,
  hasResults,
  onOpenExport,
}) => {
  return (
    <header className="h-11 bg-white border-b border-outline-variant/60 flex items-center justify-between px-4 shrink-0 shadow-xs z-30 select-none">
      {/* Brand & Privacy Badge */}
      <div className="flex items-center gap-3">
        <div className="flex items-center gap-2">
          <div className="w-6 h-6 rounded bg-primary-container flex items-center justify-center text-white font-bold text-xs shadow-xs">
            R
          </div>
          <span className="font-bold tracking-wider text-xs uppercase text-primary">
            RECONCILE
          </span>
        </div>

        <div className="h-3.5 w-px bg-outline-variant/60 mx-1" />

        <div className="inline-flex items-center gap-1.5 px-2 py-0.5 rounded bg-surface-low text-xs text-on-surface-variant font-medium">
          <ShieldCheck className="w-3.5 h-3.5 text-secondary" />
          <span>Local processing — 100% offline</span>
        </div>
      </div>

      {/* Workflow Navigation Tabs */}
      <nav className="flex items-center gap-1">
        <button
          type="button"
          onClick={() => onNavigate('import')}
          className={`flex items-center gap-1.5 px-3 py-1 rounded text-xs font-medium transition-colors cursor-pointer ${
            currentStep === 'import'
              ? 'bg-surface-low text-secondary font-semibold border border-secondary/20 shadow-xs'
              : 'text-on-surface-variant hover:text-on-surface hover:bg-gray-100'
          }`}
        >
          <FileSpreadsheet className="w-3.5 h-3.5" />
          <span>1. Import Datasets</span>
        </button>

        <span className="text-gray-300 text-xs">/</span>

        <button
          type="button"
          onClick={() => onNavigate('mapping')}
          disabled={!hasFiles}
          className={`flex items-center gap-1.5 px-3 py-1 rounded text-xs font-medium transition-colors cursor-pointer disabled:opacity-40 disabled:cursor-not-allowed ${
            currentStep === 'mapping'
              ? 'bg-surface-low text-secondary font-semibold border border-secondary/20 shadow-xs'
              : 'text-on-surface-variant hover:text-on-surface hover:bg-gray-100'
          }`}
        >
          <TableProperties className="w-3.5 h-3.5" />
          <span>2. Column Mapping</span>
        </button>

        <span className="text-gray-300 text-xs">/</span>

        <button
          type="button"
          onClick={() => onNavigate('results')}
          disabled={!hasResults}
          className={`flex items-center gap-1.5 px-3 py-1 rounded text-xs font-medium transition-colors cursor-pointer disabled:opacity-40 disabled:cursor-not-allowed ${
            currentStep === 'results' || currentStep === 'detail'
              ? 'bg-surface-low text-secondary font-semibold border border-secondary/20 shadow-xs'
              : 'text-on-surface-variant hover:text-on-surface hover:bg-gray-100'
          }`}
        >
          <GitCompare className="w-3.5 h-3.5" />
          <span>3. Reconciliation Results</span>
        </button>
      </nav>

      {/* Quick Export Action */}
      <div className="flex items-center gap-2">
        {hasResults && onOpenExport && (
          <button
            type="button"
            onClick={onOpenExport}
            className="inline-flex items-center gap-1.5 px-3 py-1 rounded bg-secondary text-white text-xs font-semibold hover:bg-secondary-container transition-all cursor-pointer shadow-xs active:scale-[0.98]"
          >
            <Download className="w-3.5 h-3.5" />
            <span>Export Excel</span>
          </button>
        )}
      </div>
    </header>
  );
};
