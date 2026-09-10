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
 *
 * Fix #5: Updated to use React Router's useLocation for scroll-to-top on navigation.
 */

import { useEffect, useRef } from 'react';
import { useLocation } from 'react-router-dom';
import Sidebar from './Sidebar';

export default function AppLayout({ onNewAudit, children }) {
  const mainRef = useRef(null);
  const location = useLocation();

  useEffect(() => {
    if (mainRef.current) {
      mainRef.current.scrollTop = 0;
    }
  }, [location.pathname]);

  return (
    <div className="h-screen max-h-screen overflow-hidden bg-slate-50 flex font-sans">
      <Sidebar onNewAudit={onNewAudit} />
      <div className="flex-1 flex flex-col min-w-0 h-full overflow-hidden pt-14 lg:pt-0">
        <main ref={mainRef} className="flex-1 px-4 sm:px-6 lg:px-8 py-6 lg:py-8 overflow-y-auto">
          <div key={location.pathname} className="max-w-7xl mx-auto page-transition pb-12">
            {children}
          </div>
        </main>
      </div>
    </div>
  );
}
