/**
 * ProcureAI - File Summary
 * 
 * What it does:
 * Confirms major destructive actions.
 * 
 * What it means:
 * Intermediary warning dialog.
 * 
 * Importance in Project:
 * Medium. Warns users before deleting audits or files.
 */

import Button from './Button';

export default function ConfirmDialog({ open, title, message, confirmLabel = 'Confirm', cancelLabel = 'Cancel', variant = 'danger', onConfirm, onCancel }) {
  if (!open) return null;

  return (
    <div className="fixed inset-0 z-[60] flex items-center justify-center p-4">
      <div className="absolute inset-0 bg-slate-900/50" onClick={onCancel} aria-hidden="true" />
      <div className="relative bg-white rounded-lg shadow-xl w-full max-w-md border border-slate-200 p-6" role="alertdialog" aria-labelledby="confirm-title">
        <h2 id="confirm-title" className="text-lg font-display font-semibold text-slate-900">{title}</h2>
        {message && <p className="mt-2 text-sm text-slate-600">{message}</p>}
        <div className="mt-6 flex justify-end gap-2">
          <Button variant="secondary" size="sm" onClick={onCancel}>{cancelLabel}</Button>
          <Button variant={variant} size="sm" onClick={onConfirm}>{confirmLabel}</Button>
        </div>
      </div>
    </div>
  );
}
