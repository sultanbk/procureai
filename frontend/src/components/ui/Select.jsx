/**
 * ProcureAI - File Summary
 * 
 * What it does:
 * Custom select dropdown.
 * 
 * What it means:
 * Standardized dropdown.
 * 
 * Importance in Project:
 * Low. Used for filtering dropdown fields.
 */

export default function Select({ className = '', children, ...props }) {
  return (
    <select
      className={`input-field appearance-none bg-white pr-8 ${className}`}
      {...props}
    >
      {children}
    </select>
  );
}
