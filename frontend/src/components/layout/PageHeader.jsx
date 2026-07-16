/**
 * ProcureAI - File Summary
 * 
 * What it does:
 * Page header displaying titles and action buttons.
 * 
 * What it means:
 * Top layout navigation bar.
 * 
 * Importance in Project:
 * Medium. Standardizes page context headers.
 */

export default function PageHeader({ title, description, back, actions, children }) {
  return (
    <div className="mb-8">
      {back && (
        <div className="mb-4">{back}</div>
      )}
      <div className="flex flex-col sm:flex-row sm:items-start sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-display font-bold text-slate-900 tracking-tight">
            {title}
          </h1>
          {description && (
            <p className="mt-1.5 text-sm text-slate-600 max-w-2xl">{description}</p>
          )}
        </div>
        {actions && (
          <div className="flex items-center gap-2 shrink-0">{actions}</div>
        )}
      </div>
      {children}
    </div>
  );
}
