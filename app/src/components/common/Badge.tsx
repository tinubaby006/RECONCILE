import type { RecordStatus } from '../../types/reconcile';

interface BadgeProps {
  status: RecordStatus | 'ready' | 'custom';
  label?: string;
  pulse?: boolean;
  className?: string;
}

export const Badge: React.FC<BadgeProps> = ({ status, label, pulse = false, className = '' }) => {
  const getStyles = () => {
    switch (status) {
      case 'matched':
        return 'bg-emerald-50 text-emerald-800 border-emerald-200';
      case 'discrepancy':
        return 'bg-rose-50 text-rose-800 border-rose-200';
      case 'needs_review':
        return 'bg-amber-50 text-amber-800 border-amber-200';
      case 'missing_in_b':
      case 'missing_in_a':
        return 'bg-red-50 text-red-700 border-red-200';
      case 'duplicate':
        return 'bg-indigo-50 text-indigo-800 border-indigo-200';
      case 'ready':
        return 'bg-secondary-fixed text-on-secondary-fixed border-secondary/20';
      default:
        return 'bg-gray-100 text-gray-800 border-gray-200';
    }
  };

  const getDotColor = () => {
    switch (status) {
      case 'matched':
        return 'bg-emerald-500';
      case 'discrepancy':
        return 'bg-rose-500';
      case 'needs_review':
        return 'bg-amber-500';
      case 'missing_in_b':
      case 'missing_in_a':
        return 'bg-red-500';
      case 'duplicate':
        return 'bg-indigo-500';
      default:
        return 'bg-gray-400';
    }
  };

  const getDefaultLabel = () => {
    switch (status) {
      case 'matched':
        return 'Matched';
      case 'discrepancy':
        return 'Discrepancy';
      case 'needs_review':
        return 'Needs Review';
      case 'missing_in_b':
        return 'Missing from B';
      case 'missing_in_a':
        return 'Missing from A';
      case 'duplicate':
        return 'Duplicate';
      case 'ready':
        return 'File Ready';
      default:
        return status;
    }
  };

  return (
    <span
      className={`inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-medium border ${getStyles()} ${className}`}
    >
      <span className={`w-1.5 h-1.5 rounded-full ${getDotColor()} ${pulse ? 'animate-pulse' : ''}`} />
      <span>{label || getDefaultLabel()}</span>
    </span>
  );
};
