"use client";

import { AlertCircle, RefreshCw, XCircle } from 'lucide-react';
import { getErrorMessage } from '@/lib/errors';

interface ErrorDisplayProps {
  error: unknown;
  onRetry?: () => void;
  title?: string;
}

export function ErrorDisplay({ error, onRetry, title }: ErrorDisplayProps) {
  const message = getErrorMessage(error);

  return (
    <div className="bg-red-500/10 border border-red-500/50 rounded-xl p-6">
      <div className="flex items-start gap-4">
        <XCircle className="w-6 h-6 text-red-400 flex-shrink-0 mt-1" />
        <div className="flex-1">
          {title && (
            <h3 className="text-lg font-semibold text-red-400 mb-2">{title}</h3>
          )}
          <p className="text-red-300">{message}</p>
          {onRetry && (
            <button
              onClick={onRetry}
              className="mt-4 px-4 py-2 bg-red-500/20 hover:bg-red-500/30 text-red-300 rounded-lg font-medium flex items-center gap-2 transition-colors"
            >
              <RefreshCw className="w-4 h-4" />
              Reintentar
            </button>
          )}
        </div>
      </div>
    </div>
  );
}

export function WarningDisplay({ message }: { message: string }) {
  return (
    <div className="bg-yellow-500/10 border border-yellow-500/50 rounded-xl p-4">
      <div className="flex items-start gap-3">
        <AlertCircle className="w-5 h-5 text-yellow-400 flex-shrink-0 mt-0.5" />
        <p className="text-yellow-300 text-sm">{message}</p>
      </div>
    </div>
  );
}
