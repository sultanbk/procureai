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
import { Bell, Mail, Save, Sliders, AlertCircle, CheckCircle2, RefreshCw, Eye, EyeOff } from 'lucide-react';
import { getNotificationSettings, updateNotificationSettings, testSlack, testEmail } from '../api';
import PageHeader from '../components/layout/PageHeader';
import Card from '../components/ui/Card';
import Button from '../components/ui/Button';
import Input from '../components/ui/Input';
import Spinner from '../components/ui/Spinner';
import { useToast } from '../components/ui/ToastProvider';

export default function Settings() {
  const { toast } = useToast();
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [testingSlack, setTestingSlack] = useState(false);
  const [testingEmail, setTestingEmail] = useState(false);

  const [slackStatus, setSlackStatus] = useState(null); // { success: bool, message: str }
  const [emailStatus, setEmailStatus] = useState(null); // { success: bool, message: str }
  const [error, setError] = useState(null);

  const [activeTab, setActiveTab] = useState('notifications'); // 'notifications' | 'rules'
  const [showSmtpPassword, setShowSmtpPassword] = useState(false);

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
                    <span className="text-sm font-semibold text-slate-900 block">Leakage Threshold Trigger (INR)</span>
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
