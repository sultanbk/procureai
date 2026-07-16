/**
 * ProcureAI - File Summary
 * 
 * What it does:
 * Organizes components into interactive tabs.
 * 
 * What it means:
 * Horizontal tabs layout switcher.
 * 
 * Importance in Project:
 * Medium. Simplifies multi-screen data inside pages.
 */

export default function Tabs({ tabs, activeTab, onChange, className = '' }) {
  return (
    <div className={`inline-flex p-1 bg-slate-100 rounded-lg border border-slate-200 ${className}`}>
      {tabs.map((tab) => (
        <button
          key={tab.id}
          type="button"
          onClick={() => onChange(tab.id)}
          className={`px-4 py-1.5 text-xs font-semibold rounded-md transition-colors ${
            activeTab === tab.id
              ? 'bg-white text-slate-900 shadow-sm'
              : 'text-slate-500 hover:text-slate-700'
          }`}
        >
          {tab.label}
        </button>
      ))}
    </div>
  );
}
