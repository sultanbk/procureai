/**
 * ProcureAI - File Summary
 * 
 * What it does:
 * Right-sliding panel overlay.
 * 
 * What it means:
 * Drawer container.
 * 
 * Importance in Project:
 * Medium. Houses secondary options and QAs.
 */

import { useEffect } from 'react';
import { createPortal } from 'react-dom';
import { X } from 'lucide-react';

export default function Drawer({ open, onClose, title, children, width = 'w-[400px]', hideHeader = false }) {
  useEffect(() => {
    if (!open) return;
    const handleKey = (e) => {
      if (e.key === 'Escape') onClose();
    };
    document.addEventListener('keydown', handleKey);
    return () => document.removeEventListener('keydown', handleKey);
  }, [open, onClose]);

  if (!open) return null;

  return createPortal(
    <div className="fixed inset-0 z-50 print:hidden flex items-stretch justify-end">
      <div 
        className="absolute inset-0 bg-slate-900/20 backdrop-blur-sm animate-in fade-in duration-300" 
        onClick={onClose} 
        aria-hidden="true" 
      />
      <aside className={`relative my-4 mr-4 ${width} max-w-[calc(100%-2rem)] bg-white rounded-2xl shadow-2xl shadow-slate-900/20 border border-slate-200/60 flex flex-col overflow-hidden animate-in slide-in-from-right duration-300 ease-out`} onClick={e => e.stopPropagation()}>
        {!hideHeader && (
          <div className="flex items-center justify-between px-5 py-4 border-b border-slate-200 bg-slate-50/50">
            <h2 className="text-base font-semibold text-slate-900 font-display">{title}</h2>
            <button
              type="button"
              onClick={onClose}
              className="p-1.5 rounded-lg text-slate-400 hover:text-slate-700 hover:bg-slate-100 transition-colors duration-200 border border-transparent hover:border-slate-200"
              aria-label="Close"
            >
              <X className="h-4.5 w-4.5 stroke-[1.5]" />
            </button>
          </div>
        )}
        <div className="flex-1 overflow-hidden flex flex-col">{children}</div>
      </aside>
    </div>,
    document.body
  );
}
