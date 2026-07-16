export default function Tooltip({ children, content, position = 'top', className = '' }) {
  const positionClasses = {
    top: 'bottom-full left-1/2 -translate-x-1/2 mb-2',
    bottom: 'top-full left-1/2 -translate-x-1/2 mt-2',
    left: 'right-full top-1/2 -translate-y-1/2 mr-2',
    right: 'left-full top-1/2 -translate-y-1/2 ml-2',
  };

  return (
    <div className="relative group inline-flex items-center justify-center">
      {children}
      <div className={`absolute z-50 invisible group-hover:visible opacity-0 group-hover:opacity-100 transition-all duration-200 w-max max-w-xs px-3 py-2 text-xs font-medium text-white bg-slate-800 rounded-md shadow-xl pointer-events-none ${positionClasses[position]} ${className}`}>
        {content}
      </div>
    </div>
  );
}
