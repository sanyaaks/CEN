import React from "react";
import { Inbox } from "lucide-react";

interface EmptyStateProps {
  title?: string;
  description?: string;
}

export default function EmptyState({
  title = "No Data Found",
  description = "There are currently no observations or index metrics for this selection."
}: EmptyStateProps) {
  return (
    <div className="w-full py-16 app-bg-surface border app-border rounded-lg flex flex-col items-center justify-center text-center space-y-2 p-6 transition-colors">
      <div className="w-10 h-10 rounded-md app-bg-card border app-border flex items-center justify-center text-[var(--color-gold)] shadow-sm">
        <Inbox className="w-5 h-5" />
      </div>
      <h4 className="text-sm font-bold app-text-primary">{title}</h4>
      <p className="text-xs app-text-secondary max-w-sm">{description}</p>
    </div>
  );
}
