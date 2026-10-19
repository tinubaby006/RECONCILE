import React from 'react';
import type { ColumnMapping, ColumnRole, DatasetMeta } from '../../types/reconcile';
import { Button } from '../common/Button';
import { 
  ArrowLeft, 
  ArrowRight, 
  CheckCircle2, 
  HelpCircle
} from 'lucide-react';

interface MappingScreenProps {
  datasetA: DatasetMeta;
  datasetB: DatasetMeta;
  mappings: ColumnMapping[];
  onUpdateMapping: (index: number, updated: Partial<ColumnMapping>) => void;
  onBack: () => void;
  onReconcile: () => void;
}

export const MappingScreen: React.FC<MappingScreenProps> = ({
  datasetA,
  datasetB,
  mappings,
  onUpdateMapping,
  onBack,
  onReconcile,
}) => {
  const getRoleBadgeStyle = (role: ColumnRole) => {
    switch (role) {
      case 'match_key':
      case 'entity':
      case 'date':
      case 'amount':
        return 'bg-secondary-fixed text-on-secondary-fixed border-secondary/20';
      case 'compare':
        return 'bg-gray-100 text-gray-700 border-gray-200';
      case 'ignore':
        return 'bg-gray-50 text-gray-400 border-gray-200';
    }
  };

  return (
    <div className="flex-1 flex flex-col p-6 max-w-6xl mx-auto w-full">
      {/* Header */}
      <div className="flex items-center justify-between pb-4 border-b border-outline-variant/40">
        <div>
          <h1 className="text-xl font-bold tracking-tight text-on-surface">Review column mapping</h1>
          <p className="text-xs text-on-surface-variant mt-1">
            Comparing <span className="font-semibold text-on-surface">{datasetA.file_name}</span> and{' '}
            <span className="font-semibold text-on-surface">{datasetB.file_name}</span>. Confirm matching roles.
          </p>
        </div>

        <div className="flex items-center gap-2">
          <Button variant="secondary" size="sm" onClick={onBack} icon={<ArrowLeft className="w-3.5 h-3.5" />}>
            Back to files
          </Button>
          <Button variant="primary" size="md" onClick={onReconcile} icon={<ArrowRight className="w-4 h-4" />}>
            Reconcile datasets
          </Button>
        </div>
      </div>

      {/* Mapping High-Density Table */}
      <div className="mt-6 bg-white rounded-lg border border-outline-variant/60 shadow-xs overflow-hidden">
        <table className="w-full text-left border-collapse text-xs">
          <thead>
            <tr className="bg-surface-low border-b border-outline-variant/50 text-[11px] font-semibold uppercase tracking-wider text-on-surface-variant">
              <th className="py-2.5 px-4">Dataset A Column</th>
              <th className="py-2.5 px-4">Sample (Dataset A)</th>
              <th className="py-2.5 px-4">Dataset B Column</th>
              <th className="py-2.5 px-4">Sample (Dataset B)</th>
              <th className="py-2.5 px-4">Field Role</th>
              <th className="py-2.5 px-4 text-right">Confidence</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-100">
            {mappings.map((m, idx) => {
              return (
                <tr key={m.col_a} className="hover:bg-gray-50/80 transition-colors">
                  {/* Col A */}
                  <td className="py-3 px-4 font-semibold text-on-surface">
                    {m.col_a}
                  </td>

                  {/* Sample A */}
                  <td className="py-3 px-4 font-mono text-gray-600 text-[11px]">
                    {m.sample_a || '—'}
                  </td>

                  {/* Col B Selector */}
                  <td className="py-3 px-4">
                    <select
                      value={m.col_b || ''}
                      onChange={(e) => {
                        const val = e.target.value || null;
                        const matchB = datasetB.columns.find((c) => c.name === val);
                        onUpdateMapping(idx, {
                          col_b: val,
                          status: val ? 'mapped' : 'unmapped',
                          sample_b: matchB?.sample_values[0]?.toString() || null,
                        });
                      }}
                      className="bg-surface-low hover:bg-surface-container font-medium text-xs text-on-surface rounded px-2 py-1 border border-outline-variant/40 outline-none cursor-pointer focus:border-secondary"
                    >
                      <option value="">[ Do not map ]</option>
                      {datasetB.columns.map((cb) => (
                        <option key={cb.name} value={cb.name}>
                          {cb.name}
                        </option>
                      ))}
                    </select>
                  </td>

                  {/* Sample B */}
                  <td className="py-3 px-4 font-mono text-gray-600 text-[11px]">
                    {m.sample_b || '—'}
                  </td>

                  {/* Role Selector */}
                  <td className="py-3 px-4">
                    <div className="flex items-center gap-1.5">
                      <select
                        value={m.role}
                        onChange={(e) =>
                          onUpdateMapping(idx, { role: e.target.value as ColumnRole })
                        }
                        className={`text-xs font-semibold uppercase px-2 py-0.5 rounded border outline-none cursor-pointer ${getRoleBadgeStyle(
                          m.role
                        )}`}
                      >
                        <option value="match_key">Key (Match ID)</option>
                        <option value="entity">Entity (Company)</option>
                        <option value="amount">Amount</option>
                        <option value="date">Date</option>
                        <option value="compare">Compare Field</option>
                        <option value="ignore">Ignore</option>
                      </select>
                    </div>
                  </td>

                  {/* Confidence Badge */}
                  <td className="py-3 px-4 text-right">
                    {m.status === 'ignored' || m.role === 'ignore' ? (
                      <span className="text-gray-400 font-mono text-[11px]">Ignored</span>
                    ) : m.col_b ? (
                      <span className="inline-flex items-center gap-1 text-emerald-700 font-medium text-xs">
                        <CheckCircle2 className="w-3.5 h-3.5" />
                        <span>{Math.round(m.confidence * 100)}%</span>
                      </span>
                    ) : (
                      <span className="text-amber-700 font-medium text-xs">Unmapped</span>
                    )}
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>

      {/* Guidance Note */}
      <div className="mt-4 flex items-start gap-2 text-xs text-on-surface-variant bg-surface-low p-3 rounded border border-secondary/10">
        <HelpCircle className="w-4 h-4 text-secondary shrink-0 mt-0.5" />
        <div>
          <span className="font-semibold text-on-surface">Mapping Guidelines: </span>
          <span>
            Assign <code className="bg-white px-1 py-0.5 rounded font-mono border">Key</code> to primary record identifiers (e.g. invoice, transaction, or check number). Assign <code className="bg-white px-1 py-0.5 rounded font-mono border">Entity</code> to party names, and <code className="bg-white px-1 py-0.5 rounded font-mono border">Amount</code> for balance tolerance checks.
          </span>
        </div>
      </div>
    </div>
  );
};
