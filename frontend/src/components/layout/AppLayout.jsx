/**
 * ProcureAI - File Summary
 * 
 * What it does:
 * Layout shell providing side navigation structural layouts.
 * 
 * What it means:
 * Main grid container wrapping child routes.
 * 
 * Importance in Project:
 * High. Maintains dashboard structural layout.
 */

import { useEffect, useRef } from 'react';
import Sidebar from './Sidebar';

export default function AppLayout({ currentView, onNavigate, onNewAudit, children }) {
  const mainRef = useRef(null);

  useEffect(() => {
    if (mainRef.current) {
      mainRef.current.scrollTop = 0;
    }
  }, [currentView]);

  return (
    <div className="min-h-screen bg-slate-50 flex font-sans">
      <Sidebar
        currentView={currentView}
        onNavigate={onNavigate}
        onNewAudit={onNewAudit}
      />
      <div className="flex-1 flex flex-col min-w-0 lg:ml-0 pt-14 lg:pt-0">
        <main ref={mainRef} className="flex-1 px-4 sm:px-6 lg:px-8 py-6 lg:py-8 overflow-y-auto">
          <div key={currentView} className="max-w-7xl mx-auto page-transition">
            {children}
          </div>
        </main>
      </div>
    </div>
  );
}
