/**
 * ProcureAI - File Summary
 * 
 * What it does:
 * Manages transient alert messages.
 * 
 * What it means:
 * Alert notification banner.
 * 
 * Importance in Project:
 * High. Notifies users of upload status or successes.
 */

import { createContext, useCallback, useContext, useState } from 'react';
import { CheckCircle2, AlertCircle, Info, X } from 'lucide-react';
import ConfirmDialog from './ConfirmDialog';

const ToastContext = createContext(null);

const ICONS = {
  success: CheckCircle2,
  error: AlertCircle,
  info: Info,
};

const STYLES = {
  success: 'bg-emerald-50 border-emerald-200 text-emerald-800',
  error: 'bg-rose-50 border-rose-200 text-rose-800',
  info: 'bg-teal-50 border-teal-200 text-teal-800',
};

export function ToastProvider({ children }) {
  const [toasts, setToasts] = useState([]);
  const [confirmState, setConfirmState] = useState(null);

  const dismiss = useCallback((id) => {
    setToasts(prev => prev.filter(t => t.id !== id));
  }, []);

  const toast = useCallback((message, type = 'info', duration = 4000) => {
    const id = Date.now() + Math.random();
    setToasts(prev => [...prev, { id, message, type }]);
    if (duration > 0) {
      setTimeout(() => dismiss(id), duration);
    }
    return id;
  }, [dismiss]);

  const confirm = useCallback(({ title, message, confirmLabel, cancelLabel, variant }) => {
    return new Promise((resolve) => {
      setConfirmState({
        title: title || 'Are you sure?',
        message,
        confirmLabel: confirmLabel || 'Confirm',
        cancelLabel: cancelLabel || 'Cancel',
        variant: variant || 'danger',
        resolve,
      });
    });
  }, []);

  const handleConfirm = () => {
    confirmState?.resolve(true);
    setConfirmState(null);
  };

  const handleCancel = () => {
    confirmState?.resolve(false);
    setConfirmState(null);
  };

  return (
    <ToastContext.Provider value={{ toast, confirm }}>
      {children}
      <div className="fixed bottom-4 right-4 z-[70] flex flex-col gap-2 max-w-sm w-full pointer-events-none print:hidden">
        {toasts.map(({ id, message, type }) => {
          const Icon = ICONS[type] || Info;
          return (
            <div
              key={id}
              className={`pointer-events-auto flex items-start gap-3 px-4 py-3 rounded-lg border shadow-card text-sm font-medium animate-in slide-in-from-bottom-2 ${STYLES[type] || STYLES.info}`}
              role="status"
            >
              <Icon className="h-5 w-5 shrink-0 mt-0.5" />
              <span className="flex-1">{message}</span>
              <button type="button" onClick={() => dismiss(id)} className="opacity-60 hover:opacity-100 shrink-0">
                <X className="h-4 w-4" />
              </button>
            </div>
          );
        })}
      </div>
      <ConfirmDialog
        open={!!confirmState}
        title={confirmState?.title}
        message={confirmState?.message}
        confirmLabel={confirmState?.confirmLabel}
        cancelLabel={confirmState?.cancelLabel}
        variant={confirmState?.variant}
        onConfirm={handleConfirm}
        onCancel={handleCancel}
      />
    </ToastContext.Provider>
  );
}

// eslint-disable-next-line react-refresh/only-export-components
export function useToast() {
  const ctx = useContext(ToastContext);
  if (!ctx) throw new Error('useToast must be used within ToastProvider');
  return ctx;
}
