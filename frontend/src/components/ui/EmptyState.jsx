/**
 * ProcureAI - File Summary
 * 
 * What it does:
 * Displays messages when tables or folders are empty.
 * 
 * What it means:
 * Placeholder display.
 * 
 * Importance in Project:
 * Low. Promotes clean UI design when database records are missing.
 */

import Button from './Button';

export default function EmptyState({ icon: Icon, title, description, actionLabel, onAction }) {
  return (
    <div className="card p-12 text-center">
      {Icon && (
        <div className="mx-auto w-16 h-16 rounded-2xl bg-slate-50 border border-slate-200/60 flex items-center justify-center mb-5 transition-transform duration-300 hover:scale-105">
          {typeof Icon === 'string' ? (
            <span className="font-mono text-lg font-bold text-slate-500">{Icon}</span>
          ) : (
            <Icon className="h-7 w-7 text-slate-400 stroke-[1.5]" />
          )}
        </div>
      )}
      <h3 className="text-lg font-semibold text-slate-900 font-display">{title}</h3>
      {description && (
        <p className="mt-2 text-sm text-slate-500 max-w-md mx-auto">{description}</p>
      )}
      {actionLabel && onAction && (
        <div className="mt-6">
          <Button onClick={onAction}>{actionLabel}</Button>
        </div>
      )}
    </div>
  );
}
