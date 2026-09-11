/**
 * ProcureAI - File Summary
 * 
 * What it does:
 * Main App component defining routes and layouts.
 * 
 * What it means:
 * React entry routing shell, integrating AppLayout and dashboard pages.
 * 
 * Importance in Project:
 * Critical. Houses React Router definitions and global hooks.
 *
 * Fix #5: Replaced manual useState view management with react-router-dom Routes.
 * Now supports URL-based navigation, bookmarks, deep linking, and browser back/forward.
 */

import { Routes, Route, Navigate, useNavigate, useParams } from 'react-router-dom';
import { useState, useCallback } from 'react';
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


// --- Wrapper components that extract route params and wire up navigation ---

function AuditRunningRoute() {
  const { auditId } = useParams();
  const navigate = useNavigate();
  const handleComplete = useCallback((report) => {
    navigate(`/audit/${auditId}/report`, { state: { report } });
  }, [auditId, navigate]);

  return (
    <AuditRunning
      auditId={auditId}
      onBack={() => navigate('/audits')}
      onComplete={handleComplete}
    />
  );
}

function AuditReportRoute() {
  const { auditId } = useParams();
  const navigate = useNavigate();
  const { toast } = useToast();
  const [report, setReport] = useState(null);
  const [loading, setLoading] = useState(!report);

  // Load report if not passed via navigation state
  useState(() => {
    (async () => {
      try {
        const data = await getAuditStatus(auditId);
        if (data.audit_report) {
          const reportWithRulebook = {
            ...data.audit_report,
            rulebook: data.audit_report?.rulebook || data.partial_results?.rulebook,
            invoice_data: data.audit_report?.invoice_data || data.partial_results?.invoice_data,
            status: data.status,
          };
          setReport(reportWithRulebook);
        }
      } catch {
        toast('Failed to load audit report details', 'error');
      } finally {
        setLoading(false);
      }
    })();
  }, [auditId]);

  if (loading && !report) return null;
  return <AuditReport report={report} onBack={() => navigate('/audits')} />;
}

function SupplierHistoryRoute({ backPath = '/suppliers' }) {
  const { supplierName } = useParams();
  const navigate = useNavigate();
  const { toast } = useToast();

  const handleSelectAudit = useCallback(async (id, status) => {
    if (status === 'COMPLETE' || status === 'PENDING_REVIEW') {
      navigate(`/audit/${id}/report`);
    } else {
      navigate(`/audit/${id}`);
    }
  }, [navigate]);

  return (
    <SupplierHistory
      supplierName={decodeURIComponent(supplierName)}
      onBack={() => navigate(backPath)}
      backLabel={backPath === '/library' ? 'Back to Contract Library' : 'Back to Scorecard'}
      onSelectAudit={handleSelectAudit}
    />
  );
}


export default function App() {
  const navigate = useNavigate();
  const { toast } = useToast();

  const handleSelectAudit = useCallback(async (id, status) => {
    if (status === 'COMPLETE' || status === 'PENDING_REVIEW') {
      navigate(`/audit/${id}/report`);
    } else {
      navigate(`/audit/${id}`);
    }
  }, [navigate]);

  const handleAuditStarted = useCallback((id) => {
    navigate(`/audit/${id}`);
  }, [navigate]);

  const handleNewAudit = useCallback(() => {
    navigate('/upload');
  }, [navigate]);

  return (
    <AppLayout onNewAudit={handleNewAudit}>
      <Routes>
        {/* Default redirect */}
        <Route path="/" element={<Navigate to="/audits" replace />} />

        {/* Audit routes */}
        <Route path="/audits" element={
          <AuditList
            onSelectAudit={handleSelectAudit}
            onNewAudit={handleNewAudit}
          />
        } />
        <Route path="/upload" element={
          <Upload onAuditStarted={handleAuditStarted} />
        } />
        <Route path="/audit/:auditId" element={<AuditRunningRoute />} />
        <Route path="/audit/:auditId/report" element={<AuditReportRoute />} />

        {/* Supplier routes */}
        <Route path="/suppliers" element={
          <SupplierScorecard
            onSelectSupplier={(name) => navigate(`/suppliers/${encodeURIComponent(name)}/history`)}
          />
        } />
        <Route path="/suppliers/:supplierName/history" element={
          <SupplierHistoryRoute backPath="/suppliers" />
        } />

        {/* Contract routes */}
        <Route path="/library" element={
          <ContractLibrary
            onSelectSupplier={(name) => navigate(`/library/suppliers/${encodeURIComponent(name)}/history`)}
          />
        } />
        <Route path="/library/suppliers/:supplierName/history" element={
          <SupplierHistoryRoute backPath="/library" />
        } />
        <Route path="/compare" element={<Compare />} />
        <Route path="/auto-audit" element={
          <AutoAudit
            onSelectAudit={handleSelectAudit}
            onGoToLibrary={() => navigate('/library')}
          />
        } />

        {/* Analytics & Settings */}
        <Route path="/analytics" element={<Analytics />} />
        <Route path="/settings" element={<Settings />} />

        {/* Fallback */}
        <Route path="*" element={<Navigate to="/audits" replace />} />
      </Routes>
    </AppLayout>
  );
}
