import React from 'react';

interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'primary' | 'secondary' | 'ghost' | 'danger';
  size?: 'sm' | 'md' | 'lg';
  icon?: React.ReactNode;
}

export const Button: React.FC<ButtonProps> = ({
  children,
  variant = 'primary',
  size = 'md',
  icon,
  className = '',
  disabled,
  ...props
}) => {
  const getVariantStyles = () => {
    switch (variant) {
      case 'primary':
        return 'bg-primary-container text-white hover:opacity-90 active:scale-[0.98] shadow-sm border border-transparent';
      case 'secondary':
        return 'bg-white text-on-surface hover:bg-gray-50 active:bg-gray-100 border border-outline-variant shadow-sm';
      case 'ghost':
        return 'bg-transparent text-on-surface-variant hover:text-on-surface hover:bg-surface-low border border-transparent';
      case 'danger':
        return 'bg-error text-white hover:bg-red-700 active:scale-[0.98] shadow-sm border border-transparent';
    }
  };

  const getSizeStyles = () => {
    switch (size) {
      case 'sm':
        return 'h-7 px-2.5 text-xs';
      case 'md':
        return 'h-8 px-3.5 text-xs font-medium';
      case 'lg':
        return 'h-9 px-4 text-sm font-semibold';
    }
  };

  return (
    <button
      className={`inline-flex items-center justify-center gap-1.5 rounded transition-all cursor-pointer disabled:opacity-50 disabled:cursor-not-allowed select-none ${getVariantStyles()} ${getSizeStyles()} ${className}`}
      disabled={disabled}
      {...props}
    >
      {icon && <span className="shrink-0">{icon}</span>}
      {children}
    </button>
  );
};
