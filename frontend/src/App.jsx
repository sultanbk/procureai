/**
 * ProcureAI - File Summary
 * 
 * What it does:
 * Main App component defining paths and layouts.
 * 
 * What it means:
 * React entry routing shell, integrating AppLayout and dashboard pages.
 * 
 * Importance in Project:
 * Critical. Houses React Router definitions and global hooks.
 */

import { useState } from 'react';
import AppLayout from './components/layout/AppLayout';
import Upload from './pages/Upload';
import AuditRunning from './pages/AuditRunning';
import AuditReport from './pages/AuditReport';
import AuditList from './pages/AuditList';
import SupplierScorecard from './pages/SupplierScorecard';
import SupplierHistory from './pages/SupplierHistory';
import Analytics from './pages/Analytics';
import Settings from './pages/Settings';
import ContractLibrary from './pages/ContractLibrary';
import AutoAudit from './pages/AutoAudit';
import Compare from './pages/Compare';
import { getAuditStatus } from './api';
import { useToast } from './components/ui/ToastProvider';

export default function App() {
  const { toast } = useToast();
  const [currentView, setCurrentView] = useState('list');
  const [activeAuditId, setActiveAuditId] = useState(null);
  const [completedReport, setCompletedReport] = useState(null);
  const [activeSupplierName, setActiveSupplierName] = useState(null);
  const [historyBackPath, setHistoryBackPath] = useState('scorecard');

  const handleSelectAudit = async (id, status) => {
    setActiveAuditId(id);
    if (status === 'COMPLETE') {
      try {
        const data = await getAuditStatus(id);
        const reportWithRulebook = { ...data.audit_report, rulebook: data.partial_results?.rulebook };
        setCompletedReport(reportWithRulebook);
        setCurrentView('report');
      } catch {
        toast('Failed to load audit report details', 'error');
      }
    } else if (status === 'FAILED') {
      setCompletedReport(null);
      setCurrentView('running');
    } else {
      setCompletedReport(null);
      setCurrentView('running');
    }
  };

  const handleAuditStarted = (id) => {
    setActiveAuditId(id);
    setCompletedReport(null);
    setCurrentView('running');
  };

  const handleAuditComplete = (report) => {
    setCompletedReport(report);
    setCurrentView('report');
  };

  const handleNewAudit = () => {
    setActiveAuditId(null);
    setCompletedReport(null);
    setCurrentView('upload');
  };

  return (
    <AppLayout
      currentView={currentView}
      onNavigate={setCurrentView}
      onNewAudit={handleNewAudit}
    >
      {currentView === 'list' && (
        <AuditList
          onSelectAudit={handleSelectAudit}
          onNewAudit={handleNewAudit}
        />
      )}
      {currentView === 'upload' && (
        <Upload onAuditStarted={handleAuditStarted} />
      )}
      {currentView === 'running' && (
        <AuditRunning
          auditId={activeAuditId}
          onBack={() => setCurrentView('list')}
          onComplete={handleAuditComplete}
        />
      )}
      {currentView === 'report' && (
        <AuditReport
          report={completedReport}
          onBack={() => setCurrentView('list')}
        />
      )}
      {currentView === 'scorecard' && (
        <SupplierScorecard
          onSelectSupplier={(name) => {
            setActiveSupplierName(name);
            setHistoryBackPath('scorecard');
            setCurrentView('history');
          }}
        />
      )}
      {currentView === 'history' && (
        <SupplierHistory
          supplierName={activeSupplierName}
          onBack={() => setCurrentView(historyBackPath)}
          backLabel={historyBackPath === 'library' ? 'Back to Contract Library' : 'Back to Scorecard'}
          onSelectAudit={handleSelectAudit}
        />
      )}
      {currentView === 'library' && (
        <ContractLibrary
          onSelectSupplier={(name) => {
            setActiveSupplierName(name);
            setHistoryBackPath('library');
            setCurrentView('history');
          }}
        />
      )}
      {currentView === 'auto-audit' && (
        <AutoAudit
          onSelectAudit={handleSelectAudit}
          onGoToLibrary={() => setCurrentView('library')}
        />
      )}
      {currentView === 'analytics' && <Analytics />}
      {currentView === 'settings' && <Settings />}
      {currentView === 'compare' && <Compare />}
    </AppLayout>
  );
}
