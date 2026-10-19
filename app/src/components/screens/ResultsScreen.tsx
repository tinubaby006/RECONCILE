import React, { useState, useMemo } from 'react';
import type { ReconciliationRecord, ReconciliationSummary } from '../../types/reconcile';
import { MetricPill } from '../common/MetricPill';
import { Badge } from '../common/Badge';
import { Button } from '../common/Button';
import { 
  Search, 
  ChevronDown, 
  ChevronRight, 
  Filter, 
  Download, 
  Layers, 
  ArrowRight,
  Eye
} from 'lucide-react';

interface ResultsScreenProps {
  summary: ReconciliationSummary;
  records: ReconciliationRecord[];
  onSelectRecord: (record: ReconciliationRecord) => void;
  onOpenExport: () => void;
}

export const ResultsScreen: React.FC<ResultsScreenProps> = ({
  summary,
  records,
  onSelectRecord,
  onOpenExport,
}) => {
  const [viewScope, setViewScope] = useState<'exceptions' | 'all'>('exceptions');
  const [searchQuery, setSearchQuery] = useState('');
  const [statusFilter, setStatusFilter] = useState<string>('all');
  const [groupByEntity, setGroupByEntity] = useState(true);
  const [expandedGroups, setExpandedGroups] = useState<Record<string, boolean>>({
    'Acme Industrial Solutions Ltd': true,
    'Globex Corporation': true,
  });

  const toggleGroup = (entityName: string) => {
    setExpandedGroups((prev) => ({
      ...prev,
      [entityName]: !prev[entityName],
    }));
  };

  // Filter records based on view scope, status filter, and search
  const filteredRecords = useMemo(() => {
    return records.filter((r) => {
      // 1. View Scope filter (Default to exceptions only)
      if (viewScope === 'exceptions' && r.status === 'matched') {
        return false;
      }

      // 2. Specific status filter
      if (statusFilter !== 'all' && r.status !== statusFilter) {
        return false;
      }

      // 3. Search query
      if (searchQuery.trim()) {
        const q = searchQuery.toLowerCase();
        const matchRef = r.reference.toLowerCase().includes(q);
        const matchEntity = r.entity.toLowerCase().includes(q);
        return matchRef || matchEntity;
      }

      return true;
    });
  }, [records, viewScope, statusFilter, searchQuery]);

  // Group filtered records by entity
  const groupedRecords = useMemo(() => {
    const map = new Map<string, ReconciliationRecord[]>();
    for (const r of filteredRecords) {
      const ent = r.entity || 'Unassigned';
      if (!map.has(ent)) {
        map.set(ent, []);
      }
      map.get(ent)!.push(r);
    }
    return map;
  }, [filteredRecords]);

  const exceptionsCount = records.filter((r) => r.status !== 'matched').length;

  return (
    <div className="flex-1 flex flex-col p-6 max-w-7xl mx-auto w-full">
      {/* Top Header Bar */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-4 border-b border-outline-variant/40">
        <div>
          <h1 className="text-xl font-bold tracking-tight text-on-surface">Reconciliation results</h1>
          <p className="text-xs text-on-surface-variant mt-0.5">
            Overview of matched records, variances, and pending review items.
          </p>
        </div>

        <Button
          variant="primary"
          size="md"
          onClick={onOpenExport}
          icon={<Download className="w-4 h-4" />}
        >
          Export Excel
        </Button>
      </div>

      {/* Summary Metric Pills Bar */}
      <div className="flex flex-wrap items-center gap-2 mt-4 bg-white p-3 rounded-lg border border-outline-variant/50 shadow-xs">
        <MetricPill
          label="Matched"
          count={summary.matched_count.toLocaleString()}
          dotColor="bg-emerald-500"
          active={statusFilter === 'matched'}
          onClick={() => {
            setViewScope('all');
            setStatusFilter(statusFilter === 'matched' ? 'all' : 'matched');
          }}
          variant="success"
        />

        <MetricPill
          label="Discrepancies"
          count={summary.discrepancies_count.toLocaleString()}
          dotColor="bg-rose-500"
          active={statusFilter === 'discrepancy'}
          onClick={() => setStatusFilter(statusFilter === 'discrepancy' ? 'all' : 'discrepancy')}
          variant="error"
        />

        <MetricPill
          label="Needs Review"
          count={summary.needs_review_count.toLocaleString()}
          dotColor="bg-amber-500"
          active={statusFilter === 'needs_review'}
          onClick={() => setStatusFilter(statusFilter === 'needs_review' ? 'all' : 'needs_review')}
          variant="warning"
        />

        <MetricPill
          label="Missing in Bank"
          count={summary.missing_in_b_count.toLocaleString()}
          dotColor="bg-red-400"
          active={statusFilter === 'missing_in_b'}
          onClick={() => setStatusFilter(statusFilter === 'missing_in_b' ? 'all' : 'missing_in_b')}
        />

        <MetricPill
          label="Missing in Ledger"
          count={summary.missing_in_a_count.toLocaleString()}
          dotColor="bg-red-400"
          active={statusFilter === 'missing_in_a'}
          onClick={() => setStatusFilter(statusFilter === 'missing_in_a' ? 'all' : 'missing_in_a')}
        />

        <MetricPill
          label="Duplicates"
          count={summary.duplicates_count.toLocaleString()}
          dotColor="bg-indigo-500"
          active={statusFilter === 'duplicate'}
          onClick={() => setStatusFilter(statusFilter === 'duplicate' ? 'all' : 'duplicate')}
        />
      </div>

      {/* Filter & View Controls */}
      <div className="flex flex-col sm:flex-row items-stretch sm:items-center justify-between gap-3 mt-4">
        {/* Exceptions vs All Records Toggle */}
        <div className="inline-flex rounded border border-outline-variant/60 p-0.5 bg-gray-100/70 text-xs shrink-0">
          <button
            type="button"
            onClick={() => setViewScope('exceptions')}
            className={`px-3 py-1 rounded font-medium transition-all cursor-pointer ${
              viewScope === 'exceptions'
                ? 'bg-white text-primary font-semibold shadow-2xs'
                : 'text-on-surface-variant hover:text-on-surface'
            }`}
          >
            Exceptions only ({exceptionsCount})
          </button>
          <button
            type="button"
            onClick={() => setViewScope('all')}
            className={`px-3 py-1 rounded font-medium transition-all cursor-pointer ${
              viewScope === 'all'
                ? 'bg-white text-primary font-semibold shadow-2xs'
                : 'text-on-surface-variant hover:text-on-surface'
            }`}
          >
            All records ({records.length})
          </button>
        </div>

        {/* Search Input */}
        <div className="relative flex-1 max-w-sm">
          <Search className="w-3.5 h-3.5 absolute left-2.5 top-1/2 -translate-y-1/2 text-gray-400 pointer-events-none" />
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Search reference or entity..."
            className="w-full h-8 pl-8 pr-3 text-xs bg-white rounded border border-outline-variant/60 text-on-surface placeholder:text-gray-400 outline-none focus:border-secondary"
          />
        </div>

        {/* Group By Entity & Filter dropdowns */}
        <div className="flex items-center gap-2">
          <button
            type="button"
            onClick={() => setGroupByEntity(!groupByEntity)}
            className={`h-8 px-2.5 rounded text-xs border flex items-center gap-1.5 transition-colors cursor-pointer ${
              groupByEntity
                ? 'bg-surface-low border-secondary/40 text-secondary font-semibold'
                : 'bg-white border-outline-variant/60 text-on-surface-variant'
            }`}
          >
            <Layers className="w-3.5 h-3.5" />
            <span>Group: Company</span>
          </button>

          <div className="relative">
            <select
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value)}
              className="h-8 pl-2.5 pr-7 rounded text-xs bg-white border border-outline-variant/60 text-on-surface font-medium outline-none cursor-pointer focus:border-secondary appearance-none"
            >
              <option value="all">Filter: All Statuses</option>
              <option value="matched">Matched</option>
              <option value="discrepancy">Discrepancies</option>
              <option value="needs_review">Needs Review</option>
              <option value="missing_in_b">Missing in B</option>
              <option value="missing_in_a">Missing in A</option>
              <option value="duplicate">Duplicates</option>
            </select>
            <Filter className="w-3 h-3 text-gray-400 absolute right-2 top-1/2 -translate-y-1/2 pointer-events-none" />
          </div>
        </div>
      </div>

      {/* Results Table */}
      <div className="mt-4 bg-white rounded-lg border border-outline-variant/60 shadow-xs overflow-hidden">
        {/* Table Column Headers */}
        <div className="grid grid-cols-12 bg-surface-low py-2.5 px-4 text-[11px] font-semibold uppercase tracking-wider text-on-surface-variant border-b border-outline-variant/50">
          <div className="col-span-2">Reference / ID</div>
          <div className="col-span-2">Entity</div>
          <div className="col-span-2">Status</div>
          <div className="col-span-2 text-right pr-4">Dataset A (Ledger)</div>
          <div className="col-span-2 text-right pr-4">Dataset B (Bank)</div>
          <div className="col-span-2 text-right">Action</div>
        </div>

        {/* Empty State */}
        {filteredRecords.length === 0 && (
          <div className="p-12 text-center text-xs text-on-surface-variant">
            No records found matching the current filters.
          </div>
        )}

        {/* Grouped or Flat Records Rendering */}
        {groupByEntity ? (
          <div className="divide-y divide-gray-100">
            {Array.from(groupedRecords.entries()).map(([entityName, entityRecs]) => {
              const isExpanded = expandedGroups[entityName] ?? true;
              const entityExceptions = entityRecs.filter((r) => r.status !== 'matched').length;
              const totalEntityVariance = entityRecs.reduce(
                (sum, r) => sum + (r.amount_diff ? Math.abs(r.amount_diff) : 0),
                0
              );

              return (
                <div key={entityName} className="flex flex-col">
                  {/* Entity Group Header Bar */}
                  <div
                    onClick={() => toggleGroup(entityName)}
                    className="flex items-center justify-between px-4 py-2 bg-gray-50/90 hover:bg-gray-100/80 cursor-pointer border-b border-gray-100 transition-colors"
                  >
                    <div className="flex items-center gap-2">
                      {isExpanded ? (
                        <ChevronDown className="w-4 h-4 text-gray-500" />
                      ) : (
                        <ChevronRight className="w-4 h-4 text-gray-500" />
                      )}
                      <span className="text-xs font-bold text-on-surface">{entityName}</span>
                      {entityExceptions > 0 && (
                        <span className="bg-rose-100 text-rose-800 text-[10px] font-semibold px-2 py-0.5 rounded-full">
                          {entityExceptions} exception{entityExceptions > 1 ? 's' : ''}
                        </span>
                      )}
                    </div>

                    <div className="text-xs text-on-surface-variant">
                      Variance:{' '}
                      <span className="font-mono font-semibold text-rose-700">
                        {totalEntityVariance > 0
                          ? `-₹${totalEntityVariance.toLocaleString(undefined, {
                              minimumFractionDigits: 2,
                            })}`
                          : '₹0.00'}
                      </span>
                    </div>
                  </div>

                  {/* Rows inside Entity Group */}
                  {isExpanded && (
                    <div className="divide-y divide-gray-100/70">
                      {entityRecs.map((rec) => renderRow(rec))}
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        ) : (
          <div className="divide-y divide-gray-100">
            {filteredRecords.map((rec) => renderRow(rec))}
          </div>
        )}
      </div>
    </div>
  );

  function renderRow(rec: ReconciliationRecord) {
    const isNeedsReview = rec.status === 'needs_review';
    return (
      <div
        key={rec.id}
        onClick={() => onSelectRecord(rec)}
        className="grid grid-cols-12 items-center py-2.5 px-4 text-xs hover:bg-surface-low/60 cursor-pointer transition-colors"
      >
        {/* Reference / ID */}
        <div className="col-span-2 font-mono font-medium text-on-surface truncate">
          {rec.reference}
        </div>

        {/* Entity */}
        <div className="col-span-2 truncate text-on-surface-variant">
          {rec.entity}
        </div>

        {/* Status */}
        <div className="col-span-2">
          <Badge status={rec.status} label={rec.status_label} pulse={isNeedsReview} />
        </div>

        {/* Dataset A */}
        <div className="col-span-2 text-right pr-4 font-mono font-medium text-on-surface">
          {rec.amount_a !== null && rec.amount_a !== undefined
            ? `₹${rec.amount_a.toLocaleString(undefined, { minimumFractionDigits: 2 })}`
            : '—'}
        </div>

        {/* Dataset B */}
        <div className="col-span-2 text-right pr-4 font-mono font-medium text-on-surface">
          {rec.amount_b !== null && rec.amount_b !== undefined
            ? `₹${rec.amount_b.toLocaleString(undefined, { minimumFractionDigits: 2 })}`
            : '—'}
        </div>

        {/* Action Button */}
        <div className="col-span-2 flex items-center justify-end gap-1.5">
          <button
            type="button"
            onClick={(e) => {
              e.stopPropagation();
              onSelectRecord(rec);
            }}
            className={`inline-flex items-center gap-1 px-2.5 py-1 rounded text-xs font-semibold cursor-pointer transition-colors ${
              isNeedsReview
                ? 'bg-amber-100 text-amber-900 hover:bg-amber-200'
                : 'bg-surface-low text-secondary hover:bg-surface-container'
            }`}
          >
            {isNeedsReview ? (
              <>
                <span>Review match</span>
                <ArrowRight className="w-3 h-3" />
              </>
            ) : (
              <>
                <Eye className="w-3 h-3" />
                <span>View details</span>
              </>
            )}
          </button>
        </div>
      </div>
    );
  }
};
