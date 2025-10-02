import React from 'react';
import { CheckCircle, AlertCircle, InfoIcon, AlertTriangle, X } from 'lucide-react';

export type AlertType = 'success' | 'error' | 'warning' | 'info';

interface AlertProps {
  type?: AlertType;
  title?: string;
  message: string;
  onClose?: () => void;
  className?: string;
}

const alertStyles = {
  success: {
    container: 'bg-green-50 border-green-500 text-green-900 dark:bg-green-900/20 dark:border-green-700 dark:text-green-200',
    icon: 'text-green-600 dark:text-green-400',
  },
  error: {
    container: 'bg-red-50 border-red-500 text-red-900 dark:bg-red-900/20 dark:border-red-700 dark:text-red-200',
    icon: 'text-red-600 dark:text-red-400',
  },
  warning: {
    container: 'bg-yellow-50 border-yellow-500 text-yellow-900 dark:bg-yellow-900/20 dark:border-yellow-700 dark:text-yellow-200',
    icon: 'text-yellow-600 dark:text-yellow-400',
  },
  info: {
    container: 'bg-blue-50 border-blue-500 text-blue-900 dark:bg-blue-900/20 dark:border-blue-700 dark:text-blue-200',
    icon: 'text-blue-600 dark:text-blue-400',
  },
};

const alertIcons = {
  success: CheckCircle,
  error: AlertCircle,
  warning: AlertTriangle,
  info: InfoIcon,
};

export function Alert({ type = 'info', title, message, onClose, className = '' }: AlertProps) {
  const Icon = alertIcons[type];
  const styles = alertStyles[type];

  return (
    <div
      className={`relative flex items-start gap-3 p-4 border rounded-lg ${styles.container} ${className}`}
      role="alert"
    >
      <Icon className={`h-5 w-5 flex-shrink-0 mt-0.5 ${styles.icon}`} />
      <div className="flex-1">
        {title && <h3 className="font-semibold mb-1">{title}</h3>}
        <p className="text-sm">{message}</p>
      </div>
      {onClose && (
        <button
          onClick={onClose}
          className="ml-auto flex-shrink-0 p-1 hover:bg-black/5 dark:hover:bg-white/5 rounded transition-colors"
          aria-label="Close"
        >
          <X className="h-4 w-4" />
        </button>
      )}
    </div>
  );
}

export default Alert;