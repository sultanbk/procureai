/**
 * ProcureAI - File Summary
 * 
 * What it does:
 * Customizable interactive buttons with loader states.
 * 
 * What it means:
 * Interactive button element.
 * 
 * Importance in Project:
 * High. Standardized action trigger across forms.
 */

const variants = {
  primary: 'bg-teal-600 hover:bg-teal-700 text-white border border-transparent shadow-sm',
  secondary: 'bg-white hover:bg-slate-50 text-slate-700 border border-slate-300 shadow-sm',
  ghost: 'bg-transparent hover:bg-slate-100 text-slate-600 border border-transparent',
  danger: 'bg-rose-600 hover:bg-rose-700 text-white border border-transparent shadow-sm',
};

const sizes = {
  sm: 'px-3 py-1.5 text-xs',
  md: 'px-4 py-2 text-sm',
  lg: 'px-5 py-2.5 text-sm',
};

export default function Button({
  variant = 'primary',
  size = 'md',
  className = '',
  children,
  ...props
}) {
  return (
    <button
      type="button"
      className={`inline-flex items-center justify-center gap-2 font-semibold rounded-md transition-colors focus:outline-none focus:ring-2 focus:ring-teal-500 focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed ${variants[variant]} ${sizes[size]} ${className}`}
      {...props}
    >
      {children}
    </button>
  );
}
