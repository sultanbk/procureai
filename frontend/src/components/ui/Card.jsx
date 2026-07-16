/**
 * ProcureAI - File Summary
 * 
 * What it does:
 * Container wrapping blocks.
 * 
 * What it means:
 * Stylized container card.
 * 
 * Importance in Project:
 * Medium. Shapes page components consistently.
 */

export default function Card({ className = '', children, header, footer, padding = true }) {
  return (
    <div className={`card ${padding ? 'p-6' : ''} ${className}`}>
      {header && (
        <div className={`${padding ? '' : 'px-6 pt-6'} border-b border-slate-200 pb-4 mb-4`}>
          {header}
        </div>
      )}
      {children}
      {footer && (
        <div className={`${padding ? '' : 'px-6 pb-6'} border-t border-slate-200 pt-4 mt-4`}>
          {footer}
        </div>
      )}
    </div>
  );
}
