import React, { useState } from 'react';
import type { ReconciliationRecord } from '../../types/reconcile';
import { Badge } from '../common/Badge';
import { Button } from '../common/Button';
import { 
  ArrowLeft, 
  CheckCircle2, 
  X, 
  Info, 
  ArrowLeftRight 
} from 'lucide-react';

interface RecordDetailScreenProps {
  record: ReconciliationRecord;
  recordIndex: number;
  totalRecords: number;
  onBack: () => void;
  onPrevRecord: () => void;
  onNextRecord: () => void;
  onConfirmMatch: (recordId: string) => void;
  onMarkUnmatched: (recordId: string) => void;
  onSwitchCandidate: (recordId: string, candidateId: string) => void;
}

export const RecordDetailScreen: React.FC<RecordDetailScreenProps> = ({
  record,
  recordIndex,
  totalRecords,
  onBack,
  onPrevRecord,
  onNextRecord,
  onConfirmMatch,
  onMarkUnmatched,
  onSwitchCandidate,
}) => {
  const [selectedCandidateId, setSelectedCandidateId] = useState<string>(
    record.candidates[0]?.candidate_id || ''
  );

  const isConfirmed = record.status === 'matched';
  const isNeedsReview = record.status === 'needs_review';

  return (
    <div className="flex-1 flex flex-col p-6 max-w-5xl mx-auto w-full pb-16">
      {/* Top Navigation & Action Bar */}
      <div className="bg-white p-4 rounded-lg border border-outline-variant/60 shadow-xs flex flex-col gap-4">
        <div className="flex items-center justify-between flex-wrap gap-2">
          {/* Breadcrumb & Pager */}
          <div className="flex items-center gap-2 text-xs">
            <button
              type="button"
              onClick={onBack}
              className="inline-flex items-center gap-1 text-secondary hover:text-primary font-medium hover:underline cursor-pointer"
            >
              <ArrowLeft className="w-3.5 h-3.5" />
              <span>Back to results</span>
            </button>
            <span className="text-gray-300">/</span>
            <span className="px-2 py-0.5 rounded bg-surface-low text-on-surface-variant font-mono font-medium text-[11px]">
              Record {recordIndex + 1} of {totalRecords}
            </span>
          </div>

          {/* Quick Record Navigation & Decision Controls */}
          <div className="flex items-center gap-2">
            <div className="flex items-center border border-outline-variant/60 rounded overflow-hidden mr-2">
              <button
                type="button"
                onClick={onPrevRecord}
                disabled={recordIndex === 0}
                className="px-2 py-1 text-xs text-on-surface-variant hover:bg-gray-100 disabled:opacity-40 disabled:cursor-not-allowed cursor-pointer"
              >
                Previous
              </button>
              <div className="w-px h-4 bg-gray-200" />
              <button
                type="button"
                onClick={onNextRecord}
                disabled={recordIndex === totalRecords - 1}
                className="px-2 py-1 text-xs text-on-surface-variant hover:bg-gray-100 disabled:opacity-40 disabled:cursor-not-allowed cursor-pointer"
              >
                Next
              </button>
            </div>

            <Button
              variant="secondary"
              size="sm"
              onClick={() => onMarkUnmatched(record.id)}
              icon={<X className="w-3.5 h-3.5 text-rose-600" />}
            >
              Mark as Unmatched
            </Button>

            <Button
              variant="primary"
              size="sm"
              onClick={() => onConfirmMatch(record.id)}
              disabled={isConfirmed}
              icon={<CheckCircle2 className="w-3.5 h-3.5 text-white" />}
            >
              {isConfirmed ? 'Match Confirmed' : 'Confirm Match'}
            </Button>
          </div>
        </div>

        {/* Record Header & Status */}
        <div className="flex items-center justify-between pt-2 border-t border-gray-100">
          <div className="flex items-center gap-2">
            <h1 className="text-lg font-bold text-on-surface font-mono">{record.reference}</h1>
            <span className="text-gray-300 font-light">•</span>
            <span className="text-sm font-semibold text-on-surface-variant">{record.entity}</span>
          </div>

          <Badge status={record.status} label={record.status_label} pulse={isNeedsReview} />
        </div>
      </div>

      {/* Discrepancy Explanation Banner */}
      {record.differences.length > 0 && (
        <div className="mt-4 flex items-start gap-3 bg-surface-low p-3.5 rounded-lg border border-secondary/20 shadow-2xs">
          <div className="w-7 h-7 rounded bg-secondary-fixed text-secondary flex items-center justify-center shrink-0 mt-0.5">
            <Info className="w-4 h-4" />
          </div>
          <div className="flex-1 text-xs">
            <span className="font-semibold text-on-surface block mb-0.5">Discrepancy Notes</span>
            <ul className="list-disc pl-4 space-y-0.5 text-on-surface-variant">
              {record.differences.map((d, idx) => (
                <li key={idx}>
                  {d.description}{' '}
                  {d.delta !== null && d.delta !== undefined && (
                    <span className="font-mono font-semibold text-rose-700 bg-rose-50 px-1 py-0.2 rounded border border-rose-200">
                      {d.delta > 0 ? `+${d.delta}` : d.delta}
                    </span>
                  )}
                </li>
              ))}
            </ul>
          </div>
        </div>
      )}

      {/* Side-by-Side Comparison Canvas */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mt-4">
        {/* Dataset A Card */}
        <div className="bg-white rounded-lg border border-outline-variant/60 shadow-xs overflow-hidden">
          <div className="px-4 py-2.5 bg-gray-50/90 border-b border-gray-200 flex items-center justify-between">
            <div className="flex items-center gap-2">
              <span className="w-2 h-2 rounded-full bg-primary" />
              <span className="text-xs font-bold text-primary">Dataset A: Internal AP Ledger</span>
            </div>
            <span className="text-[10px] bg-white border border-gray-200 px-2 py-0.5 rounded font-medium text-gray-700">
              Source Record
            </span>
          </div>

          <div className="p-4 space-y-3 text-xs">
            <div className="flex items-center justify-between py-1.5 px-2.5 rounded bg-surface-low">
              <span className="text-on-surface-variant font-medium">Reference</span>
              <span className="font-mono font-semibold text-primary">{record.reference}</span>
            </div>

            <div className="flex items-center justify-between py-1.5 px-2.5 rounded bg-surface-low">
              <span className="text-on-surface-variant font-medium">Entity / Name</span>
              <span className="font-medium text-on-surface">{record.entity}</span>
            </div>

            <div className="flex items-center justify-between py-1.5 px-2.5 rounded bg-surface-low">
              <span className="text-on-surface-variant font-medium">Date</span>
              <span className="font-mono text-on-surface">{record.date_a || '—'}</span>
            </div>

            <div className="flex items-center justify-between py-2 px-2.5 rounded bg-surface-high/60 border border-secondary/20">
              <span className="font-bold text-primary">Amount</span>
              <span className="font-mono text-sm font-bold text-on-surface">
                {record.amount_a !== null && record.amount_a !== undefined
                  ? `₹${record.amount_a.toLocaleString(undefined, { minimumFractionDigits: 2 })}`
                  : '—'}
              </span>
            </div>

            <div className="flex items-center justify-between py-1.5 px-2.5 rounded bg-gray-50 text-gray-500 text-[11px]">
              <span>Source Location</span>
              <span className="font-mono">{record.source_a || '—'}</span>
            </div>
          </div>
        </div>

        {/* Dataset B Card */}
        <div className="bg-white rounded-lg border border-outline-variant/60 shadow-xs overflow-hidden">
          <div className="px-4 py-2.5 bg-gray-50/90 border-b border-gray-200 flex items-center justify-between">
            <div className="flex items-center gap-2">
              <span className="w-2 h-2 rounded-full bg-secondary" />
              <span className="text-xs font-bold text-secondary">Dataset B: Bank Statement</span>
            </div>
            <span className="text-[10px] bg-secondary-fixed text-on-secondary-fixed border border-secondary/20 px-2 py-0.5 rounded font-medium">
              Comparison Record
            </span>
          </div>

          <div className="p-4 space-y-3 text-xs">
            <div className="flex items-center justify-between py-1.5 px-2.5 rounded bg-surface-low">
              <span className="text-on-surface-variant font-medium">Reference</span>
              <span className="font-mono font-semibold text-secondary">
                {record.record_b ? String(record.record_b['Ref_No'] || record.reference) : '—'}
              </span>
            </div>

            <div className="flex items-center justify-between py-1.5 px-2.5 rounded bg-surface-low">
              <span className="text-on-surface-variant font-medium">Entity / Name</span>
              <span className="font-medium text-on-surface">
                {record.record_b ? String(record.record_b['Entity'] || record.entity) : '—'}
              </span>
            </div>

            <div className="flex items-center justify-between py-1.5 px-2.5 rounded bg-surface-low">
              <span className="text-on-surface-variant font-medium">Date</span>
              <span className="font-mono text-on-surface">{record.date_b || '—'}</span>
            </div>

            <div
              className={`flex items-center justify-between py-2 px-2.5 rounded border ${
                record.amount_diff && Math.abs(record.amount_diff) > 0.01
                  ? 'bg-rose-50 border-rose-200 text-rose-900'
                  : 'bg-surface-high/60 border-secondary/20 text-on-surface'
              }`}
            >
              <div className="flex flex-col">
                <span className="font-bold">Amount</span>
                {record.amount_diff && Math.abs(record.amount_diff) > 0.01 && (
                  <span className="text-[10px] text-rose-700 font-medium">
                    Diff: {record.amount_diff > 0 ? `+${record.amount_diff}` : record.amount_diff}
                  </span>
                )}
              </div>
              <span className="font-mono text-sm font-bold">
                {record.amount_b !== null && record.amount_b !== undefined
                  ? `₹${record.amount_b.toLocaleString(undefined, { minimumFractionDigits: 2 })}`
                  : '—'}
              </span>
            </div>

            <div className="flex items-center justify-between py-1.5 px-2.5 rounded bg-gray-50 text-gray-500 text-[11px]">
              <span>Source Location</span>
              <span className="font-mono">{record.source_b || '—'}</span>
            </div>
          </div>
        </div>
      </div>

      {/* Alternate Candidate Counterparts */}
      {record.candidates && record.candidates.length > 0 && (
        <div className="mt-4 bg-white rounded-lg border border-outline-variant/60 shadow-xs p-4">
          <div className="flex items-center justify-between pb-3 border-b border-gray-100">
            <div className="flex items-center gap-2">
              <ArrowLeftRight className="w-4 h-4 text-secondary" />
              <h2 className="text-xs font-bold text-on-surface">
                Possible candidate matches in Bank Statement
              </h2>
            </div>
            <span className="text-[11px] text-on-surface-variant">
              {record.candidates.length} candidate{record.candidates.length > 1 ? 's' : ''} evaluated
            </span>
          </div>

          <div className="mt-3 space-y-2">
            {record.candidates.map((cand) => {
              const isSelected = selectedCandidateId === cand.candidate_id;
              return (
                <div
                  key={cand.candidate_id}
                  onClick={() => setSelectedCandidateId(cand.candidate_id)}
                  className={`flex items-center justify-between p-3 rounded border text-xs cursor-pointer transition-all ${
                    isSelected
                      ? 'bg-surface-low border-secondary shadow-2xs'
                      : 'bg-gray-50/60 border-gray-200 hover:bg-gray-50'
                  }`}
                >
                  <div className="flex items-center gap-3">
                    <input
                      type="radio"
                      name="candidateSelection"
                      checked={isSelected}
                      onChange={() => setSelectedCandidateId(cand.candidate_id)}
                      className="cursor-pointer text-secondary"
                    />
                    <div>
                      <div className="flex items-center gap-2">
                        <span className="font-semibold text-on-surface">{cand.source_b}</span>
                        <span className="text-gray-300">•</span>
                        <span className="font-mono font-bold text-primary">
                          ₹{cand.amount_b?.toLocaleString(undefined, { minimumFractionDigits: 2 })}
                        </span>
                        <span className="text-on-surface-variant text-[11px]">({cand.date_b})</span>
                      </div>
                      <p className="text-[11px] text-on-surface-variant mt-0.5">{cand.reason}</p>
                    </div>
                  </div>

                  <div className="flex items-center gap-2">
                    <span className="font-mono text-xs font-bold text-secondary bg-white px-2 py-0.5 rounded border border-secondary/20">
                      {Math.round(cand.score)}% Match
                    </span>
                    <Button
                      variant="secondary"
                      size="sm"
                      onClick={(e) => {
                        e.stopPropagation();
                        onSwitchCandidate(record.id, cand.candidate_id);
                      }}
                    >
                      Switch to this record
                    </Button>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}
    </div>
  );
};
