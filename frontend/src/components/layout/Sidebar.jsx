/**
 * ProcureAI - Sidebar Navigation
 *
 * Fix #5: Replaced prop-based onNavigate/currentView with React Router's
 * useNavigate/useLocation for URL-based navigation with bookmarks and deep linking.
 */

import { useState } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { FileText, Award, BarChart2, FolderOpen, Columns, Zap, Settings, Plus, Menu, X } from 'lucide-react';

const NAV_GROUPS = [
  {
    label: 'Audits',
    items: [
      { path: '/audits', label: 'Audit History', icon: FileText, alsoActive: ['/audit/', '/upload'] },
    ],
  },
  {
    label: 'Suppliers',
    items: [
      { path: '/suppliers', label: 'Scorecard', icon: Award, alsoActive: ['/suppliers/'] },
      { path: '/analytics', label: 'Analytics', icon: BarChart2 },
    ],
  },
  {
    label: 'Contracts',
    items: [
      { path: '/library', label: 'Contract Library', icon: FolderOpen },
      { path: '/compare', label: 'Compare', icon: Columns },
      { path: '/auto-audit', label: 'Auto-Audit', icon: Zap },
    ],
  },
  {
    label: 'System',
    items: [
      { path: '/settings', label: 'Settings', icon: Settings },
    ],
  },
];

function isItemActive(item, pathname) {
  if (pathname === item.path) return true;
  if (item.alsoActive?.some(prefix => pathname.startsWith(prefix))) return true;
  return false;
}

function isAuditFlowActive(pathname) {
  return ['/upload'].includes(pathname) || pathname.startsWith('/audit/');
}

function NavContent({ onNewAudit, onClose }) {
  const navigate = useNavigate();
  const location = useLocation();
  const pathname = location.pathname;

  const handleNav = (path) => {
    navigate(path);
    onClose?.();
  };

  const auditFlowActive = isAuditFlowActive(pathname);

  return (
    <div className="flex flex-col h-full">
      <div className="p-5 border-b border-slate-200">
        <button
          type="button"
          onClick={() => handleNav('/audits')}
          className="flex items-center gap-3 w-full text-left group animate-fade-in"
        >
          <img src="/Prodapt-icon-logo.png" alt="Prodapt Logo" className="h-12 w-12 object-contain" />
          <div>
            <div className="flex items-center gap-2">
              <span className="font-display font-extrabold text-slate-900 text-2xl">
                ProcureAI
              </span>
              <span className="px-1.5 py-0.5 text-[8px] font-bold bg-blue-100 text-blue-700 rounded-full tracking-wider">
                BETA
              </span>
            </div>

            <span className="text-[10px] uppercase font-bold text-slate-400 tracking-wider">
              by Prodapt
            </span>
          </div>
        </button>
      </div>

      <div className="p-4">
        <button
          type="button"
          onClick={() => {
            onNewAudit();
            onClose?.();
          }}
          className={`w-full flex items-center justify-center gap-2 px-4 py-2.5 rounded-lg text-xs font-bold uppercase tracking-wider transition-all duration-200 hover:-translate-y-0.5 ${auditFlowActive
            ? 'bg-teal-700 text-white ring-2 ring-teal-300 ring-offset-2'
            : 'bg-teal-600 hover:bg-teal-700 text-white shadow-sm'
            }`}
        >
          <Plus className="h-4 w-4 stroke-[1.5]" />
          New Audit
        </button>
      </div>

      <nav className="flex-1 overflow-y-auto px-3 pb-4 space-y-6">
        {NAV_GROUPS.map((group) => (
          <div key={group.label}>
            <p className="px-3 mb-2 text-[9px] font-bold uppercase tracking-wider text-slate-400">
              {group.label}
            </p>
            <ul className="space-y-1">
              {group.items.map((item) => {
                const active = isItemActive(item, pathname);
                return (
                   <li key={item.path}>
                    <button
                      type="button"
                      onClick={() => handleNav(item.path)}
                      className={`w-full flex items-center gap-2.5 px-3 py-2 text-xs font-bold uppercase tracking-wider transition-all duration-150 ${active
                        ? 'bg-teal-50 text-teal-800 border-l-4 border-teal-600 rounded-l-none'
                        : 'text-slate-600 hover:bg-slate-100 hover:text-slate-900 border-l-4 border-transparent'
                        }`}
                    >
                      {item.icon && <item.icon className={`h-4 w-4 stroke-[1.5] ${active ? 'text-teal-700' : 'text-slate-400 hover:text-slate-700'}`} />}
                      {item.label}
                    </button>
                  </li>
                );
              })}
            </ul>
          </div>
        ))}
      </nav>

      <div className="p-4 border-t border-slate-200">
        <div className="flex items-center justify-between text-[10px] font-bold uppercase tracking-wider text-slate-400">
          <span>
            © 2026 Procure AI
          </span>

          <span className="px-2 py-1 bg-slate-100 text-slate-600 rounded">
            v2.0
          </span>
        </div>
      </div>
    </div>
  );
}

export default function Sidebar({ onNewAudit }) {
  const [mobileOpen, setMobileOpen] = useState(false);
  const navigate = useNavigate();

  return (
    <>
      <div className="lg:hidden fixed top-0 left-0 right-0 z-40 bg-white border-b border-slate-200 px-4 py-3 flex items-center justify-between print:hidden">
        <button
          type="button"
          onClick={() => navigate('/audits')}
          className="flex items-center gap-2"
        >
          <img src="/Prodapt-icon-logo.png" alt="Prodapt Logo" className="h-6 w-6 object-contain" />
          <span className="font-display font-bold text-slate-900 text-sm">ProcureAI</span>
        </button>
        <button
          type="button"
          onClick={() => setMobileOpen(true)}
          className="p-1.5 border border-slate-200 rounded-lg text-slate-700 hover:bg-slate-50 flex items-center justify-center"
          aria-label="Open menu"
        >
          <Menu className="h-4.5 w-4.5 stroke-[1.5]" />
        </button>
      </div>

      {mobileOpen && (
        <div className="lg:hidden fixed inset-0 z-50 print:hidden">
          <div
            className="absolute inset-0 bg-slate-900/40 animate-fade-in"
            onClick={() => setMobileOpen(false)}
            aria-hidden="true"
          />
          <aside className="absolute left-0 top-0 bottom-0 w-64 bg-white shadow-xl flex flex-col">
            <button
              type="button"
              onClick={() => setMobileOpen(false)}
              className="absolute top-4 right-4 p-1.5 border border-slate-200 rounded-lg text-slate-500 hover:bg-slate-50 hover:text-slate-700 flex items-center justify-center"
              aria-label="Close menu"
            >
              <X className="h-4 w-4 stroke-[1.5]" />
            </button>
            <NavContent
              onNewAudit={onNewAudit}
              onClose={() => setMobileOpen(false)}
            />
          </aside>
        </div>
      )}

      <aside className="hidden lg:flex lg:flex-col lg:w-60 lg:shrink-0 bg-white border-r border-slate-200 h-screen sticky top-0 print:hidden">
        <NavContent
          onNewAudit={onNewAudit}
        />
      </aside>
    </>
  );
}
