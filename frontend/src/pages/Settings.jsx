/**
 * ProcureAI - File Summary
 * 
 * What it does:
 * Configure thresholds, API keys, and simulation targets.
 * 
 * What it means:
 * Control panel settings page.
 * 
 * Importance in Project:
 * Medium. Centralized configuration screen.
 */

import { useState, useEffect } from 'react';
import {
  Bell, Mail, Save, Sliders, AlertCircle, CheckCircle2, RefreshCw, Eye, EyeOff,
  Network, Database, GitBranch, Sparkles, ShieldCheck, Play, Plus, Trash2, Key, Check, Copy, Layers
} from 'lucide-react';
import {
  getNotificationSettings, updateNotificationSettings, testSlack, testEmail,
  getContextSubstrateStatus, queryContextSubstrate,
  getContextProviders, deleteContextProvider
} from '../api';
import PageHeader from '../components/layout/PageHeader';
import Card from '../components/ui/Card';
import Button from '../components/ui/Button';
import Input from '../components/ui/Input';
import Spinner from '../components/ui/Spinner';
import { useToast } from '../components/ui/ToastProvider';
import ReasoningSubgraphModal from '../components/ReasoningSubgraphModal';
import RetrievalPassCard from '../components/RetrievalPassCard';
import CreateProviderModal from '../components/CreateProviderModal';

export default function Settings() {
  const { toast } = useToast();
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [testingSlack, setTestingSlack] = useState(false);
  const [testingEmail, setTestingEmail] = useState(false);

  const [slackStatus, setSlackStatus] = useState(null); // { success: bool, message: str }
  const [emailStatus, setEmailStatus] = useState(null); // { success: bool, message: str }
  const [error, setError] = useState(null);

  const [activeTab, setActiveTab] = useState('notifications'); // 'notifications' | 'rules' | 'substrate'
  const [showSmtpPassword, setShowSmtpPassword] = useState(false);

  // Context Substrate Diagnostics State
  const [substrateStatus, setSubstrateStatus] = useState(null);
  const [substrateLoading, setSubstrateLoading] = useState(false);
  const [diagnosticResult, setDiagnosticResult] = useState(null);
  const [testingDiagnostic, setTestingDiagnostic] = useState(false);
  const [isDiagnosticGraphOpen, setIsDiagnosticGraphOpen] = useState(false);

  // Context Provider State
  const [providers, setProviders] = useState([]);
  const [isCreateModalOpen, setIsCreateModalOpen] = useState(false);
  const [activeProviderId, setActiveProviderId] = useState('procureai-default');

  // Form States
  const [slackEnabled, setSlackEnabled] = useState(false);
  const [slackWebhookUrl, setSlackWebhookUrl] = useState('');

  const [emailEnabled, setEmailEnabled] = useState(false);
  const [emailTo, setEmailTo] = useState('');
  const [emailFrom, setEmailFrom] = useState('');
  const [smtpHost, setSmtpHost] = useState('');
  const [smtpPort, setSmtpPort] = useState(587);
  const [smtpUser, setSmtpUser] = useState('');
  const [smtpPassword, setSmtpPassword] = useState('');

  const [alertOnCritical, setAlertOnCritical] = useState(true);
  const [alertOnHigh, setAlertOnHigh] = useState(false);
  const [alertThresholdInr, setAlertThresholdInr] = useState(10000);
  const [alertOnAnyFinding, setAlertOnAnyFinding] = useState(false);

  // Load Settings
  useEffect(() => {
    getNotificationSettings()
      .then((data) => {
        setSlackEnabled(data.slack_enabled);
        setSlackWebhookUrl(data.slack_webhook_url || '');
        setEmailEnabled(data.email_enabled);
        setEmailTo(data.email_to || '');
        setEmailFrom(data.email_from || '');
        setSmtpHost(data.smtp_host || '');
        setSmtpPort(data.smtp_port ?? 587);
        setSmtpUser(data.smtp_user || '');
        setSmtpPassword(data.smtp_password || '');
        setAlertOnCritical(data.alert_on_critical);
        setAlertOnHigh(data.alert_on_high);
        setAlertThresholdInr(data.alert_threshold_inr ?? 10000);
        setAlertOnAnyFinding(data.alert_on_any_finding);
        setLoading(false);
      })
      .catch((err) => {
        setError(err.message || 'Failed to load settings.');
        setLoading(false);
      });

    // Load Substrate Status
    getContextSubstrateStatus()
      .then(setSubstrateStatus)
      .catch((err) => console.warn('Context Substrate status check:', err));

    // Load Registered Context Providers
    getContextProviders()
      .then((list) => {
        setProviders(list);
        if (list.length > 0 && !list.some((p) => p.id === activeProviderId)) {
          setActiveProviderId(list[0].id);
        }
      })
      .catch((err) => console.warn('Failed to load Context Providers:', err));
  }, []);

  // Save Settings Handler
  const handleSave = async (e) => {
    e?.preventDefault();
    setSaving(true);

    const payload = {
      slack_enabled: slackEnabled,
      slack_webhook_url: slackWebhookUrl || null,
      email_enabled: emailEnabled,
      email_to: emailTo || null,
      email_from: emailFrom || null,
      smtp_host: smtpHost || null,
      smtp_port: parseInt(smtpPort) || 587,
      smtp_user: smtpUser || null,
      smtp_password: smtpPassword || null,
      alert_on_critical: alertOnCritical,
      alert_on_high: alertOnHigh,
      alert_threshold_inr: parseFloat(alertThresholdInr) || 0,
      alert_on_any_finding: alertOnAnyFinding
    };

    try {
      await updateNotificationSettings(payload);
      toast('Settings saved successfully', 'success');
    } catch (err) {
      toast(err.message || 'Failed to save settings.', 'error');
    } finally {
      setSaving(false);
    }
  };

  // Test Slack Webhook
  const handleTestSlack = async () => {
    if (!slackWebhookUrl) {
      setSlackStatus({ success: false, message: 'Please input a Webhook URL first.' });
      return;
    }
    setTestingSlack(true);
    setSlackStatus(null);
    try {
      const res = await testSlack(slackWebhookUrl);
      if (res.success) {
        setSlackStatus({ success: true, message: '✓ Test message sent!' });
      } else {
        setSlackStatus({ success: false, message: `✗ Failed: ${res.error}` });
      }
    } catch (err) {
      setSlackStatus({ success: false, message: `✗ Failed: ${err.message}` });
    } finally {
      setTestingSlack(false);
    }
  };

  // Test SMTP Email Settings
  const handleTestEmail = async () => {
    if (!emailTo || !smtpHost) {
      setEmailStatus({ success: false, message: 'Recipient email and SMTP Host are required for testing.' });
      return;
    }
    setTestingEmail(true);
    setEmailStatus(null);

    const payload = {
      email_to: emailTo,
      email_from: emailFrom || null,
      smtp_host: smtpHost,
      smtp_port: parseInt(smtpPort) || 587,
      smtp_user: smtpUser || null,
      smtp_password: smtpPassword || null
    };

    try {
      const res = await testEmail(payload);
      if (res.success) {
        setEmailStatus({ success: true, message: '✓ Test email sent successfully!' });
      } else {
        setEmailStatus({ success: false, message: `✗ Failed: ${res.error}` });
      }
    } catch (err) {
      setEmailStatus({ success: false, message: `✗ Failed: ${err.message}` });
    } finally {
      setTestingEmail(false);
    }
  };

  if (loading) {
    return (
      <div className="py-24 flex justify-center">
        <Spinner className="h-8 w-8" label="Loading settings..." />
      </div>
    );
  }

  return (
    <div className="w-full max-w-4xl mx-auto space-y-6">
      <PageHeader
        title="Alert &amp; Notification Engine Settings"
        description="Configure real-time Slack channels, SMTP mailer coordinates, and compliance audit alert conditions."
      />

      {error && (
        <div className="bg-rose-50 border border-rose-200 text-rose-700 px-4 py-3 rounded-lg text-sm font-medium animate-fade-in">
          {error}
        </div>
      )}

      {/* Modern Segmented Navigation Tabs */}
      <div className="flex border-b border-slate-200 gap-6">
        <button
          type="button"
          onClick={() => setActiveTab('notifications')}
          className={`pb-3 font-semibold text-xs uppercase tracking-wider transition-all relative border-b-2 ${
            activeTab === 'notifications'
              ? 'text-teal-600 border-teal-600'
              : 'text-slate-500 border-transparent hover:text-slate-800'
          }`}
        >
          Notification Channels
        </button>
        <button
          type="button"
          onClick={() => setActiveTab('rules')}
          className={`pb-3 font-semibold text-xs uppercase tracking-wider transition-all relative border-b-2 ${
            activeTab === 'rules'
              ? 'text-teal-600 border-teal-600'
              : 'text-slate-500 border-transparent hover:text-slate-800'
          }`}
        >
          Compliance Alerts &amp; Filters
        </button>
        <button
          type="button"
          onClick={() => setActiveTab('substrate')}
          className={`pb-3 font-semibold text-xs uppercase tracking-wider transition-all relative border-b-2 flex items-center gap-1.5 ${
            activeTab === 'substrate'
              ? 'text-indigo-600 border-indigo-600'
              : 'text-slate-500 border-transparent hover:text-slate-800'
          }`}
        >
          <Network className="w-3.5 h-3.5 text-indigo-500" />
          Context Substrate (Knowledge Brain)
        </button>
      </div>

      <div className="space-y-6">
        {activeTab === 'notifications' && (
          <div className="space-y-6 animate-fade-in">
            {/* Section 1: Slack Webhooks */}
            <Card className="space-y-4">
              <div className="flex items-center justify-between border-b border-slate-200 pb-4 -mt-2">
                <h3 className="text-xs font-bold text-slate-900 flex items-center gap-2 uppercase tracking-wide">
                  <Bell className="h-4 w-4 text-teal-600 stroke-[1.5]" />
                  Slack Notification Webhook Channel
                </h3>

                <button
                  type="button"
                  onClick={() => setSlackEnabled(!slackEnabled)}
                  className={`relative inline-flex h-5 w-9 items-center rounded-full transition-colors focus:outline-none focus:ring-2 focus:ring-teal-500 focus:ring-offset-2 ${
                    slackEnabled ? 'bg-teal-600' : 'bg-slate-300'
                  }`}
                >
                  <span
                    className={`inline-block h-3.5 w-3.5 transform rounded-full bg-white transition-transform shadow-sm ${
                      slackEnabled ? 'translate-x-4' : 'translate-x-1'
                    }`}
                  />
                </button>
              </div>

              {slackEnabled && (
                <div className="space-y-4 pt-2">
                  <div className="space-y-2">
                    <label className="text-[10px] font-bold text-slate-700 uppercase tracking-wide block">
                      Incoming Webhook URL
                    </label>
                    <div className="flex gap-3">
                      <Input
                        type="url"
                        value={slackWebhookUrl}
                        onChange={(e) => setSlackWebhookUrl(e.target.value)}
                        placeholder="https://hooks.slack.com/services/..."
                        className="flex-1"
                      />
                      <Button
                        type="button"
                        variant="secondary"
                        disabled={testingSlack}
                        onClick={handleTestSlack}
                        className="font-semibold"
                      >
                        {testingSlack && <RefreshCw className="h-4 w-4 animate-spin" />}
                        Test Connection
                      </Button>
                    </div>
                  </div>

                  {slackStatus && (
                    <div className={`p-3 rounded-lg border text-sm font-medium flex items-center gap-2 animate-fade-in ${
                      slackStatus.success
                        ? 'bg-emerald-50 border-emerald-200 text-emerald-700'
                        : 'bg-rose-50 border-rose-200 text-rose-700'
                    }`}>
                      {slackStatus.success ? <CheckCircle2 className="h-4 w-4 stroke-[1.5]" /> : <AlertCircle className="h-4 w-4 stroke-[1.5]" />}
                      <span>{slackStatus.message}</span>
                    </div>
                  )}
                </div>
              )}
            </Card>

            {/* Section 2: SMTP Mailer */}
            <Card className="space-y-4">
              <div className="flex items-center justify-between border-b border-slate-200 pb-4 -mt-2">
                <h3 className="text-xs font-bold text-slate-900 flex items-center gap-2 uppercase tracking-wide">
                  <Mail className="h-4 w-4 text-teal-600 stroke-[1.5]" />
                  SMTP Email Dispatch Coordinates
                </h3>

                <button
                  type="button"
                  onClick={() => setEmailEnabled(!emailEnabled)}
                  className={`relative inline-flex h-5 w-9 items-center rounded-full transition-colors focus:outline-none focus:ring-2 focus:ring-teal-500 focus:ring-offset-2 ${
                    emailEnabled ? 'bg-teal-600' : 'bg-slate-300'
                  }`}
                >
                  <span
                    className={`inline-block h-3.5 w-3.5 transform rounded-full bg-white transition-transform shadow-sm ${
                      emailEnabled ? 'translate-x-4' : 'translate-x-1'
                    }`}
                  />
                </button>
              </div>

              {emailEnabled && (
                <div className="space-y-4 pt-2">
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div className="space-y-1.5">
                      <label className="text-[10px] font-bold text-slate-700 uppercase tracking-wide">
                        Recipient Address (comma-separated list)
                      </label>
                      <Input
                        type="text"
                        value={emailTo}
                        onChange={(e) => setEmailTo(e.target.value)}
                        placeholder="audit-alerts@company.com, procurement@company.com"
                      />
                    </div>

                    <div className="space-y-1.5">
                      <label className="text-[10px] font-bold text-slate-700 uppercase tracking-wide">
                        From Address
                      </label>
                      <Input
                        type="email"
                        value={emailFrom}
                        onChange={(e) => setEmailFrom(e.target.value)}
                        placeholder="procureai@company.com"
                      />
                    </div>
                  </div>

                  <div className="grid grid-cols-3 gap-4">
                    <div className="col-span-2 space-y-1.5">
                      <label className="text-[10px] font-bold text-slate-700 uppercase tracking-wide">
                        SMTP Host
                      </label>
                      <Input
                        type="text"
                        value={smtpHost}
                        onChange={(e) => setSmtpHost(e.target.value)}
                        placeholder="smtp.gmail.com"
                      />
                    </div>

                    <div className="space-y-1.5">
                      <label className="text-[10px] font-bold text-slate-700 uppercase tracking-wide">
                        SMTP Port
                      </label>
                      <Input
                        type="number"
                        value={smtpPort}
                        onChange={(e) => setSmtpPort(e.target.value)}
                      />
                    </div>
                  </div>

                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div className="space-y-1.5">
                      <label className="text-[10px] font-bold text-slate-700 uppercase tracking-wide">
                        SMTP Username
                      </label>
                      <Input
                        type="text"
                        value={smtpUser}
                        onChange={(e) => setSmtpUser(e.target.value)}
                        placeholder="username"
                      />
                    </div>

                    <div className="space-y-1.5">
                      <label className="text-[10px] font-bold text-slate-700 uppercase tracking-wide">
                        SMTP Password
                      </label>
                      <div className="relative">
                        <input
                          type={showSmtpPassword ? "text" : "password"}
                          value={smtpPassword}
                          onChange={(e) => setSmtpPassword(e.target.value)}
                          placeholder="••••••••••••"
                          className="input-field pr-10"
                        />
                        <button
                          type="button"
                          onClick={() => setShowSmtpPassword(!showSmtpPassword)}
                          className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-600 focus:outline-none"
                          title={showSmtpPassword ? "Hide password" : "Show password"}
                        >
                          {showSmtpPassword ? (
                            <EyeOff className="h-4 w-4 stroke-[1.5]" />
                          ) : (
                            <Eye className="h-4 w-4 stroke-[1.5]" />
                          )}
                        </button>
                      </div>
                    </div>
                  </div>

                  <div className="pt-2">
                    <Button
                      type="button"
                      variant="secondary"
                      disabled={testingEmail}
                      onClick={handleTestEmail}
                      className="font-semibold"
                    >
                      {testingEmail && <RefreshCw className="h-4 w-4 animate-spin" />}
                      Test Email Configuration
                    </Button>
                  </div>

                  {emailStatus && (
                    <div className={`p-3 rounded-lg border text-sm font-medium flex items-center gap-2 animate-fade-in ${
                      emailStatus.success
                        ? 'bg-emerald-50 border-emerald-200 text-emerald-700'
                        : 'bg-rose-50 border-rose-200 text-rose-700'
                    }`}>
                      {emailStatus.success ? <CheckCircle2 className="h-4 w-4 stroke-[1.5]" /> : <AlertCircle className="h-4 w-4 stroke-[1.5]" />}
                      <span>{emailStatus.message}</span>
                    </div>
                  )}
                </div>
              )}
            </Card>
          </div>
        )}

        {activeTab === 'rules' && (
          <div className="space-y-6 animate-fade-in">
            {/* Section 3: Alert Conditions */}
            <Card className="space-y-5">
              <h3 className="text-xs font-bold text-slate-900 flex items-center gap-2 uppercase tracking-wide border-b border-slate-200 pb-4 -mt-2">
                <Sliders className="h-4 w-4 text-teal-600 stroke-[1.5]" />
                Operational Alert &amp; Filtering Conditions
              </h3>

              <div className="space-y-4">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <label className="flex items-center gap-3 bg-slate-50 p-4 rounded-lg border border-slate-200 cursor-pointer hover:border-teal-200 transition-colors">
                    <input
                      type="checkbox"
                      checked={alertOnCritical}
                      onChange={(e) => setAlertOnCritical(e.target.checked)}
                      className="h-4 w-4 rounded border-slate-300 text-teal-600 focus:ring-teal-500"
                    />
                    <div>
                      <span className="text-sm font-semibold text-slate-900 block">Alert on CRITICAL Finding</span>
                      <span className="text-xs text-slate-500">Instantly notify whenever a Critical violation is audit-flagged.</span>
                    </div>
                  </label>

                  <label className="flex items-center gap-3 bg-slate-50 p-4 rounded-lg border border-slate-200 cursor-pointer hover:border-teal-200 transition-colors">
                    <input
                      type="checkbox"
                      checked={alertOnHigh}
                      onChange={(e) => setAlertOnHigh(e.target.checked)}
                      className="h-4 w-4 rounded border-slate-300 text-teal-600 focus:ring-teal-500"
                    />
                    <div>
                      <span className="text-sm font-semibold text-slate-900 block">Alert on HIGH Finding</span>
                      <span className="text-xs text-slate-500">Instantly notify whenever a High violation is audit-flagged.</span>
                    </div>
                  </label>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <label className="flex items-center gap-3 bg-slate-50 p-4 rounded-lg border border-slate-200 cursor-pointer hover:border-teal-200 transition-colors">
                    <input
                      type="checkbox"
                      checked={alertOnAnyFinding}
                      onChange={(e) => setAlertOnAnyFinding(e.target.checked)}
                      className="h-4 w-4 rounded border-slate-300 text-teal-600 focus:ring-teal-500"
                    />
                    <div>
                      <span className="text-sm font-semibold text-slate-900 block">Alert on Any Finding</span>
                      <span className="text-xs text-slate-500">Trigger notification for any discrepancy regardless of severity.</span>
                    </div>
                  </label>

                  <div className="bg-slate-50 p-4 rounded-lg border border-slate-200 flex flex-col justify-center space-y-2">
                    <span className="text-sm font-semibold text-slate-900 block">Leakage Threshold Trigger ($ USD)</span>
                    <div className="relative">
                      <span className="absolute left-3 top-2.5 text-sm font-semibold text-slate-500">$</span>
                      <Input
                        type="number"
                        value={alertThresholdInr}
                        onChange={(e) => setAlertThresholdInr(e.target.value)}
                        placeholder="10000"
                        className="pl-8"
                      />
                    </div>
                    <span className="text-xs text-slate-500">Alert if total recoverable leakage matches or exceeds this amount.</span>
                  </div>
                </div>
              </div>
            </Card>
          </div>
        )}

        {/* Section 3: SynaptAI Context Substrate (4-Store Epistemic Brain) */}
        {activeTab === 'substrate' && (
          <div className="space-y-6 animate-fade-in">
            {/* System Status & Diagnostics Card */}
            <Card className="space-y-5">
              <div className="flex flex-col sm:flex-row sm:items-center justify-between border-b border-slate-200 pb-4 gap-3 -mt-2">
                <div>
                  <h3 className="text-xs font-bold text-slate-900 flex items-center gap-2 uppercase tracking-wide">
                    <Network className="h-4 w-4 text-indigo-600 stroke-[1.5]" />
                    SynaptAI Context Substrate Engine
                  </h3>
                  <p className="text-xs text-slate-500 mt-0.5">
                    Governed 4-store knowledge substrate: Neo4j Concept Graph + Milvus KS/PS/GN.
                  </p>
                </div>

                <div className="flex items-center gap-2">
                  <span className="inline-flex items-center gap-1 text-xs font-bold px-3 py-1 rounded-full bg-emerald-50 text-emerald-700 border border-emerald-200 font-mono">
                    <ShieldCheck className="w-3.5 h-3.5" />
                    {substrateStatus?.status?.toUpperCase() || 'ACTIVE (EMBEDDED)'}
                  </span>
                  <button
                    type="button"
                    onClick={() => {
                      getContextSubstrateStatus().then(setSubstrateStatus);
                      toast('Status refreshed.', 'info');
                    }}
                    className="p-1.5 text-slate-400 hover:text-slate-600 hover:bg-slate-100 rounded-lg transition-colors"
                    title="Refresh Substrate Status"
                  >
                    <RefreshCw className="w-3.5 h-3.5" />
                  </button>
                </div>
              </div>

              {/* Substrate Metadata Grid */}
              <div className="grid grid-cols-2 md:grid-cols-4 gap-3 text-xs">
                <div className="bg-slate-50 p-3 rounded-lg border border-slate-200/80">
                  <span className="text-[10px] uppercase font-bold text-slate-400 tracking-wider">Engine Mode</span>
                  <p className="text-sm font-mono font-bold text-indigo-600 mt-1 uppercase">
                    {substrateStatus?.mode || 'AUTO-FALLBACK'}
                  </p>
                </div>
                <div className="bg-slate-50 p-3 rounded-lg border border-slate-200/80">
                  <span className="text-[10px] uppercase font-bold text-slate-400 tracking-wider">Neo4j Concept Graph</span>
                  <p className="text-sm font-mono font-bold text-emerald-600 mt-1">
                    Connected ({substrateStatus?.node_count || 11} nodes)
                  </p>
                </div>
                <div className="bg-slate-50 p-3 rounded-lg border border-slate-200/80">
                  <span className="text-[10px] uppercase font-bold text-slate-400 tracking-wider">Milvus Procedural (PS)</span>
                  <p className="text-sm font-mono font-bold text-indigo-600 mt-1">
                    {substrateStatus?.procedures_count || 2} SOP DAGs Active
                  </p>
                </div>
                <div className="bg-slate-50 p-3 rounded-lg border border-slate-200/80">
                  <span className="text-[10px] uppercase font-bold text-slate-400 tracking-wider">Provider Subgraph ID</span>
                  <p className="text-xs font-mono font-semibold text-slate-700 mt-1 truncate">
                    {substrateStatus?.provider_id || 'procureai-default'}
                  </p>
                </div>
              </div>

              {/* 4-Store Architecture Breakdown */}
              <div className="space-y-3 pt-2">
                <h4 className="text-xs font-bold text-slate-800 uppercase tracking-wider">
                  4-Store Unified Epistemic Topology
                </h4>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-3 text-xs">
                  <div className="p-3 bg-indigo-50/40 border border-indigo-100 rounded-lg space-y-1">
                    <div className="flex items-center gap-1.5 font-bold text-indigo-900 text-xs">
                      <Network className="w-3.5 h-3.5 text-indigo-600" />
                      1. Neo4j Concept Graph
                    </div>
                    <p className="text-[11px] text-slate-600 leading-relaxed">
                      Entities, concepts, propositions, and multi-hop relationships. Governs amendment supersessions via <code className="font-mono bg-white px-1 py-0.5 rounded border border-indigo-200 text-red-600">SUPERSEDES</code> and <code className="font-mono bg-white px-1 py-0.5 rounded border border-indigo-200 text-emerald-600">GOVERNED_BY</code> edges.
                    </p>
                  </div>

                  <div className="p-3 bg-blue-50/40 border border-blue-100 rounded-lg space-y-1">
                    <div className="flex items-center gap-1.5 font-bold text-blue-900 text-xs">
                      <Database className="w-3.5 h-3.5 text-blue-600" />
                      2. Milvus KS (Knowledge Store)
                    </div>
                    <p className="text-[11px] text-slate-600 leading-relaxed">
                      Dense text embeddings across contract chunks. Provides semantic passage retrieval, heading hierarchy, and verbatim evidence citations.
                    </p>
                  </div>

                  <div className="p-3 bg-pink-50/40 border border-pink-100 rounded-lg space-y-1">
                    <div className="flex items-center gap-1.5 font-bold text-pink-900 text-xs">
                      <GitBranch className="w-3.5 h-3.5 text-pink-600" />
                      3. Milvus PS (Procedural Store)
                    </div>
                    <p className="text-[11px] text-slate-600 leading-relaxed">
                      Corporate Standard Operating Procedures indexed as Directed Acyclic Graphs (DAGs) with <code className="font-mono bg-white px-1 py-0.5 rounded border border-pink-200 text-pink-700">PRECEDES</code> sequential steps for dispute recovery.
                    </p>
                  </div>

                  <div className="p-3 bg-purple-50/40 border border-purple-100 rounded-lg space-y-1">
                    <div className="flex items-center gap-1.5 font-bold text-purple-900 text-xs">
                      <Sparkles className="w-3.5 h-3.5 text-purple-600" />
                      4. Milvus GN (Graph Node Index)
                    </div>
                    <p className="text-[11px] text-slate-600 leading-relaxed">
                      Embedded node signatures mapped directly to Neo4j IDs. Bridges semantic vector search directly to graph anchor entry points without fuzzy string matching.
                    </p>
                  </div>
                </div>
              </div>

              {/* Diagnostic Test Runner */}
              <div className="pt-4 border-t border-slate-200 space-y-3">
                <div className="flex items-center justify-between">
                  <div>
                    <h4 className="text-xs font-bold text-slate-800 uppercase tracking-wider">
                      Live Subgraph Traversal Diagnostic
                    </h4>
                    <p className="text-xs text-slate-500 mt-0.5">
                      Send a benchmark multi-hop question to verify graph anchoring, BFS expansion, and 5-stage pass scoring.
                    </p>
                  </div>

                  <Button
                    type="button"
                    disabled={testingDiagnostic}
                    onClick={async () => {
                      setTestingDiagnostic(true);
                      try {
                        const res = await queryContextSubstrate({
                          query: "What is the revised bandwidth rate under Amendment 1?",
                          provider_id: substrateStatus?.provider_id || "procureai-default",
                          top_k: 5,
                          hops: 2,
                        });
                        setDiagnosticResult(res);
                        toast('Diagnostic traversal completed successfully.', 'success');
                      } catch (err) {
                        toast(err.message || 'Diagnostic failed', 'error');
                      } finally {
                        setTestingDiagnostic(false);
                      }
                    }}
                    className="flex items-center gap-1.5 font-bold bg-indigo-600 hover:bg-indigo-700 text-white"
                  >
                    {testingDiagnostic ? (
                      <RefreshCw className="w-3.5 h-3.5 animate-spin" />
                    ) : (
                      <Play className="w-3.5 h-3.5 fill-current" />
                    )}
                    <span>{testingDiagnostic ? 'Traversing Graph...' : 'Run Diagnostic Query'}</span>
                  </Button>
                </div>

                {/* Diagnostic Result Display */}
                {diagnosticResult && (
                  <div className="mt-4 p-4 rounded-xl border border-indigo-100 bg-indigo-50/30 space-y-4 animate-in fade-in duration-200">
                    <div className="flex items-start justify-between gap-3">
                      <div>
                        <span className="text-[10px] font-mono uppercase tracking-wide font-bold text-indigo-600">
                          Grounded Response
                        </span>
                        <p className="text-xs text-slate-900 font-medium mt-1 leading-relaxed">
                          {diagnosticResult.answer}
                        </p>
                      </div>
                      <Button
                        type="button"
                        onClick={() => setIsDiagnosticGraphOpen(true)}
                        size="sm"
                        className="bg-white hover:bg-indigo-50 text-indigo-700 border border-indigo-200 shrink-0 flex items-center gap-1 font-semibold text-xs"
                      >
                        <Network className="w-3.5 h-3.5 text-indigo-600" />
                        View Subgraph
                      </Button>
                    </div>

                    {/* Embed 5-Stage Retrieval Pass Card */}
                    {diagnosticResult.retrieval_pass_card && (
                      <RetrievalPassCard passCard={diagnosticResult.retrieval_pass_card} />
                    )}
                  </div>
                )}
              </div>
            </Card>

            {/* Context Providers & Client IDs Card */}
            <Card className="space-y-4">
              <div className="flex flex-col sm:flex-row sm:items-center justify-between border-b border-slate-200 pb-4 gap-3 -mt-2">
                <div>
                  <h3 className="text-xs font-bold text-slate-900 flex items-center gap-2 uppercase tracking-wide">
                    <Layers className="h-4 w-4 text-indigo-600 stroke-[1.5]" />
                    Context Providers &amp; S2S Client Credentials
                  </h3>
                  <p className="text-xs text-slate-500 mt-0.5">
                    Isolated knowledge namespaces. Each provider owns its own Neo4j subgraph, vector collections, and Client ID.
                  </p>
                </div>

                <Button
                  type="button"
                  onClick={() => setIsCreateModalOpen(true)}
                  className="flex items-center gap-1.5 font-bold bg-indigo-600 hover:bg-indigo-700 text-white text-xs shadow-sm"
                >
                  <Plus className="w-3.5 h-3.5" />
                  <span>Create Provider</span>
                </Button>
              </div>

              {/* Provider List Grid */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-3.5 pt-1">
                {providers.map((p) => {
                  const isActive = activeProviderId === p.id;
                  const isDefault = p.id === 'procureai-default';

                  return (
                    <div
                      key={p.id}
                      className={`p-4 rounded-xl border transition-all flex flex-col justify-between ${
                        isActive
                          ? 'bg-indigo-50/40 border-indigo-300 shadow-sm'
                          : 'bg-white border-slate-200 hover:border-slate-300'
                      }`}
                    >
                      <div className="space-y-2.5">
                        <div className="flex items-start justify-between gap-2">
                          <div>
                            <div className="flex items-center gap-2">
                              <h4 className="font-bold text-slate-900 text-xs">{p.name}</h4>
                              {isActive && (
                                <span className="inline-flex items-center gap-1 text-[10px] font-bold px-2 py-0.5 rounded-full bg-emerald-100 text-emerald-800">
                                  <span className="w-1.5 h-1.5 rounded-full bg-emerald-600" /> Active Namespace
                                </span>
                              )}
                            </div>
                            <p className="text-[11px] text-slate-500 mt-1 line-clamp-2 leading-relaxed">
                              {p.description || 'No description provided'}
                            </p>
                          </div>
                        </div>

                        {/* Badges */}
                        <div className="flex flex-wrap gap-1.5 pt-1">
                          <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-slate-100 text-slate-700 font-semibold">
                            packet: {p.knowledge_pack_packet}
                          </span>
                          <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-purple-50 text-purple-700 border border-purple-200 font-semibold">
                            mode: {p.extraction_mode}
                          </span>
                          <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-blue-50 text-blue-700 border border-blue-200 font-semibold">
                            platform: {p.target_platform}
                          </span>
                          <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-slate-100 text-slate-600">
                            depth: {p.context_depth_limit} hops
                          </span>
                        </div>

                        {/* Client ID Pill */}
                        <div className="bg-slate-50 p-2 rounded-lg border border-slate-200/80 flex items-center justify-between gap-2">
                          <div className="flex items-center gap-1.5 truncate">
                            <Key className="w-3 h-3 text-amber-500 shrink-0" />
                            <span className="text-[10px] font-mono text-slate-600 truncate font-semibold">
                              {p.client_id}
                            </span>
                          </div>
                          <button
                            type="button"
                            onClick={() => {
                              navigator.clipboard.writeText(p.client_id);
                              toast('Client ID copied to clipboard.', 'info');
                            }}
                            className="text-slate-400 hover:text-slate-700 p-1"
                            title="Copy Client ID"
                          >
                            <Copy className="w-3 h-3" />
                          </button>
                        </div>
                      </div>

                      {/* Card Actions Footer */}
                      <div className="pt-3 border-t border-slate-100 mt-3 flex items-center justify-between text-xs">
                        {!isActive ? (
                          <button
                            type="button"
                            onClick={() => {
                              setActiveProviderId(p.id);
                              toast(`Switched active provider to: ${p.name}`, 'success');
                            }}
                            className="text-xs font-semibold text-indigo-600 hover:text-indigo-800 transition-colors"
                          >
                            Set as Active Scope
                          </button>
                        ) : (
                          <span className="text-[11px] font-medium text-slate-400">Current Scope</span>
                        )}

                        {!isDefault && (
                          <button
                            type="button"
                            onClick={async () => {
                              if (window.confirm(`Are you sure you want to delete '${p.name}'?`)) {
                                try {
                                  await deleteContextProvider(p.id);
                                  setProviders(providers.filter((x) => x.id !== p.id));
                                  toast('Provider deleted.', 'info');
                                } catch (err) {
                                  toast(err.message || 'Failed to delete provider', 'error');
                                }
                              }
                            }}
                            className="p-1 text-slate-400 hover:text-rose-600 transition-colors"
                            title="Delete Provider"
                          >
                            <Trash2 className="w-3.5 h-3.5" />
                          </button>
                        )}
                      </div>
                    </div>
                  );
                })}
              </div>
            </Card>

            {/* Create Provider 3-Step Wizard Modal */}
            <CreateProviderModal
              isOpen={isCreateModalOpen}
              onClose={() => setIsCreateModalOpen(false)}
              onCreated={(newProvider) => {
                setProviders((prev) => [...prev, newProvider]);
                setActiveProviderId(newProvider.id);
                toast(`Provider '${newProvider.name}' successfully provisioned!`, 'success');
              }}
            />

            {/* Diagnostic Subgraph Modal */}
            <ReasoningSubgraphModal
              isOpen={isDiagnosticGraphOpen}
              onClose={() => setIsDiagnosticGraphOpen(false)}
              subgraph={diagnosticResult?.reasoning_subgraph}
              title="Context Substrate: Diagnostic Traversal Subgraph"
              subtitle="Live Neo4j concept graph slice with semantic anchors"
            />
          </div>
        )}

        {/* Save Bar */}
        <div className="pt-2 flex justify-end">
          <Button
            type="button"
            disabled={saving}
            onClick={handleSave}
            size="lg"
            className="font-bold flex items-center gap-2"
          >
            {saving ? <RefreshCw className="h-4 w-4 animate-spin" /> : <Save className="h-4 w-4 stroke-[1.5]" />}
            Save Settings
          </Button>
        </div>
      </div>
    </div>
  );
}
