import React from 'react';

interface MetricPillProps {
  label: string;
  count: number | string;
  dotColor?: string;
  active?: boolean;
  onClick?: () => void;
  variant?: 'default' | 'error' | 'warning' | 'success';
}

export const MetricPill: React.FC<MetricPillProps> = ({
  label,
  count,
  dotColor = 'bg-gray-400',
  active = false,
  onClick,
  variant = 'default',
}) => {
  const getVariantStyles = () => {
    switch (variant) {
      case 'error':
        return active
          ? 'bg-rose-100 border-rose-300 text-rose-900 ring-1 ring-rose-400'
          : 'bg-rose-50/80 border-rose-200 text-rose-800 hover:bg-rose-100';
      case 'warning':
        return active
          ? 'bg-amber-100 border-amber-300 text-amber-900 ring-1 ring-amber-400'
          : 'bg-amber-50/80 border-amber-200 text-amber-800 hover:bg-amber-100';
      case 'success':
        return active
          ? 'bg-emerald-100 border-emerald-300 text-emerald-900 ring-1 ring-emerald-400'
          : 'bg-emerald-50/80 border-emerald-200 text-emerald-800 hover:bg-emerald-100';
      default:
        return active
          ? 'bg-surface-low border-secondary text-secondary ring-1 ring-secondary'
          : 'bg-surface-lowest border-outline-variant/60 text-on-surface-variant hover:bg-gray-50';
    }
  };

  return (
    <button
      type="button"
      onClick={onClick}
      className={`inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-medium border transition-all cursor-pointer shadow-xs ${getVariantStyles()}`}
    >
      <span className={`w-2 h-2 rounded-full ${dotColor}`} />
      <span>{label}:</span>
      <strong className="font-semibold text-on-surface font-mono">{count}</strong>
    </button>
  );
};
