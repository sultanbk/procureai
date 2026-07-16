/**
 * ProcureAI - File Summary
 * 
 * What it does:
 * Displays colored status badges.
 * 
 * What it means:
 * Status pill.
 * 
 * Importance in Project:
 * Medium. Highlights risk levels and audit states.
 */

const variants = {
  critical: 'badge-critical',
  high: 'badge-high',
  medium: 'badge-medium',
  low: 'badge-low',
  success: 'badge-success',
  brand: 'badge-brand',
  default: 'badge-low',
};

export default function Badge({ variant = 'default', className = '', children }) {
  return (
    <span className={`${variants[variant] || variants.default} ${className}`}>
      {children}
    </span>
  );
}

// eslint-disable-next-line react-refresh/only-export-components
export function severityVariant(severity) {
  switch (severity) {
    case 'CRITICAL': return 'critical';
    case 'HIGH': return 'high';
    case 'MEDIUM': return 'medium';
    default: return 'low';
  }
}
