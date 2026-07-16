/**
 * ProcureAI - File Summary
 * 
 * What it does:
 * Pop-up overlay modal.
 * 
 * What it means:
 * Floating overlay wrapper.
 * 
 * Importance in Project:
 * Medium. Houses dialogue sheets and forms.
 */

import { useEffect } from 'react';
import { createPortal } from 'react-dom';
import { X } from 'lucide-react';

export default function Modal({ open, isOpen, onClose, title, children, footer, maxWidth = 'max-w-2xl', flexBody = false }) {
  const isModalOpen = open ?? isOpen;

  useEffect(() => {
    if (!isModalOpen) return;
    const handleKey = (e) => {
      if (e.key === 'Escape') onClose();
    };
    document.addEventListener('keydown', handleKey);
    document.body.style.overflow = 'hidden';
    return () => {
      document.removeEventListener('keydown', handleKey);
      document.body.style.overflow = '';
    };
  }, [isModalOpen, onClose]);

  if (!isModalOpen) return null;

  return createPortal(
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 print:hidden">
      <div className="absolute inset-0 bg-slate-900/50 backdrop-blur-sm transition-all duration-300" onClick={onClose} aria-hidden="true" />
      <div className={`relative bg-white rounded-2xl shadow-2xl w-full ${maxWidth} ${flexBody ? 'h-[75vh] min-h-[500px]' : ''} max-h-[90vh] flex flex-col border border-slate-200/60 overflow-hidden transform transition-all`}>
        <div className="flex items-center justify-between px-6 py-4 border-b border-slate-100 bg-slate-50/50">
          <h2 className="text-lg font-semibold text-slate-900 font-display">{title}</h2>
          <button
            type="button"
            onClick={onClose}
            className="p-1.5 rounded-lg text-slate-400 hover:text-slate-700 hover:bg-slate-100 transition-colors duration-200 border border-transparent hover:border-slate-200"
            aria-label="Close"
          >
            <X className="h-4.5 w-4.5 stroke-[1.5]" />
          </button>
        </div>
        <div className={`flex-1 px-6 py-4 ${flexBody ? 'flex flex-col min-h-0 overflow-hidden' : 'overflow-y-auto'}`}>
          {children}
        </div>
        {footer && (
          <div className="px-6 py-4 border-t border-slate-200 flex justify-end gap-2 shrink-0">{footer}</div>
        )}
      </div>
    </div>,
    document.body
  );
}
