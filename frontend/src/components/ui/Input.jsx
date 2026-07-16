/**
 * ProcureAI - File Summary
 * 
 * What it does:
 * Input wrapper for search fields.
 * 
 * What it means:
 * Standardized input element.
 * 
 * Importance in Project:
 * Medium. Standardizes form inputs.
 */

export default function Input({ className = '', icon: Icon, ...props }) {
  if (Icon) {
    return (
      <div className="relative">
        <Icon className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-400 pointer-events-none" />
        <input className={`input-field pl-9 ${className}`} {...props} />
      </div>
    );
  }
  return <input className={`input-field ${className}`} {...props} />;
}
