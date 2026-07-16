/**
 * ProcureAI - File Summary
 * 
 * What it does:
 * Wraps grid components with standard styling.
 * 
 * What it means:
 * Standard table layout.
 * 
 * Importance in Project:
 * Medium. Structures audit tables.
 */

export function Table({ className = '', children, ...props }) {
  return (
    <div className="overflow-x-auto rounded-lg border border-slate-200">
      <table className={`w-full text-sm text-left ${className}`} {...props}>{children}</table>
    </div>
  );
}

export function TableHead({ children, ...props }) {
  return (
    <thead className="bg-slate-50 border-b border-slate-200 text-xs font-semibold uppercase tracking-wide text-slate-500" {...props}>
      {children}
    </thead>
  );
}

export function TableBody({ children, ...props }) {
  return <tbody className="divide-y divide-slate-100 bg-white" {...props}>{children}</tbody>;
}

export function TableRow({ className = '', children, onClick, ...props }) {
  return (
    <tr
      className={`table-row-hover ${onClick ? 'cursor-pointer' : ''} ${className}`}
      onClick={onClick}
      {...props}
    >
      {children}
    </tr>
  );
}

export function TableCell({ className = '', children, header, colSpan, ...props }) {
  const Tag = header ? 'th' : 'td';
  return (
    <Tag colSpan={colSpan} className={`px-4 py-3 ${header ? 'font-semibold' : 'text-slate-700'} ${className}`} {...props}>
      {children}
    </Tag>
  );
}
