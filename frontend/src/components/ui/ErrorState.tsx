import React from "react";
import { AlertCircle, RefreshCw } from "lucide-react";

interface ErrorStateProps {
  message?: string;
  onRetry?: () => void;
}

export default function ErrorState({
  message = "An error occurred while communicating with the backend API.",
  onRetry
}: ErrorStateProps) {
  return (
    <div className="w-full p-6 app-badge-rose rounded-lg flex flex-col items-center justify-center text-center space-y-3 shadow-sm">
      <AlertCircle className="w-6 h-6 text-[var(--color-rose)]" />
      <div className="space-y-1">
        <h4 className="text-sm font-bold text-[var(--color-rose)]">API Connection Error</h4>
        <p className="text-xs app-text-secondary max-w-md">{message}</p>
      </div>
      {onRetry && (
        <button
          onClick={onRetry}
          className="inline-flex items-center gap-1.5 px-3 py-1.5 app-bg-card hover:app-bg-card-hover border app-border text-xs font-semibold app-text-primary rounded-md transition-colors shadow-sm"
        >
          <RefreshCw className="w-3.5 h-3.5" />
          Retry Request
        </button>
      )}
    </div>
  );
}
