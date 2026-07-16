/**
 * ProcureAI - File Summary
 * 
 * What it does:
 * Displays visual loading indicator.
 * 
 * What it means:
 * Loading spinner.
 * 
 * Importance in Project:
 * Low. Enhances visual UX during server calls.
 */

export default function Spinner({ className = 'h-5 w-5', label = 'Loading...' }) {
  return (
    <div className="flex items-center justify-center gap-2 text-slate-500" role="status">
      <svg
        className={`animate-spin ${className}`}
        xmlns="http://www.w3.org/2000/svg"
        fill="none"
        viewBox="0 0 24 24"
        aria-hidden="true"
      >
        <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
        <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
      </svg>
      {label && <span className="text-sm">{label}</span>}
    </div>
  );
}
