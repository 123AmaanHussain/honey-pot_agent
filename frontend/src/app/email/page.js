"use client";

import { useState, useEffect } from 'react';
import { getEmailConfigStatus, setEmailConfig, startEmailMonitor, stopEmailMonitor, getEmailStatus, getEmailOutput } from '../../lib/api';
import styles from './page.module.css';

export default function EmailMonitorPage() {
  const [status, setStatus] = useState(null);
  const [output, setOutput] = useState([]);
  const [loading, setLoading] = useState(false);
  const [autoRefresh, setAutoRefresh] = useState(true);
  const [imapHost, setImapHost] = useState('');
  const [imapPort, setImapPort] = useState('993');
  const [imapUser, setImapUser] = useState('');
  const [imapPass, setImapPass] = useState('');
  const [configSet, setConfigSet] = useState(false);

  // Fetch status
  const fetchStatus = async () => {
    const result = await getEmailStatus();
    setStatus(result);
  };

  // Fetch output
  const fetchOutput = async () => {
    const result = await getEmailOutput(30);
    if (result.output) {
      setOutput(result.output);
    }
  };

  // Check if config is already set
  const checkConfigStatus = async () => {
    const result = await getEmailConfigStatus();
    if (result.config_set) {
      setConfigSet(true);
    }
  };

  // Set email config
  const handleSetConfig = async () => {
    if (!imapHost.trim() || !imapUser.trim() || !imapPass.trim()) {
      alert('Please fill in all required fields');
      return;
    }
    setLoading(true);
    const result = await setEmailConfig(imapHost, imapPort, imapUser, imapPass);
    setLoading(false);
    if (result.error) {
      alert(`Error: ${result.error}`);
    } else {
      setConfigSet(true);
      alert('Email configuration set successfully');
    }
  };

  // Start monitor
  const handleStart = async () => {
    if (!configSet) {
      alert('Please set the email configuration first');
      return;
    }
    setLoading(true);
    const result = await startEmailMonitor();
    setLoading(false);
    if (result.error) {
      alert(`Error: ${result.error}`);
    } else {
      setTimeout(fetchStatus, 2000);
    }
  };

  // Stop monitor
  const handleStop = async () => {
    setLoading(true);
    const result = await stopEmailMonitor();
    setLoading(false);
    if (result.error) {
      alert(`Error: ${result.error}`);
    } else {
      setTimeout(fetchStatus, 1000);
    }
  };

  // Auto-refresh status and output
  useEffect(() => {
    if (autoRefresh) {
      const interval = setInterval(() => {
        fetchStatus();
        fetchOutput();
      }, 5000);
      return () => clearInterval(interval);
    }
  }, [autoRefresh]);

  // Initial load
  useEffect(() => {
    checkConfigStatus();
    fetchStatus();
    fetchOutput();
  }, []);

  return (
    <div className="slide-up">
      <header className={styles.header}>
        <h1 className={styles.title}>Email Monitor</h1>
        <p className={styles.subtitle}>
          Control and monitor the email scam detection system from here.
        </p>
      </header>

      {/* Email Config Input */}
      <div className={styles.configSection}>
        <h2 className={styles.configTitle}>
          {configSet ? 'Email Configuration (Already Set)' : 'Enter Email Configuration'}
        </h2>
        <p className={styles.configDescription}>
          {configSet 
            ? 'Your email configuration is saved. You can start the monitor directly or update the configuration if needed.'
            : 'To use the email monitor, you need to provide IMAP credentials for your email account.'
          }
        </p>
        <div className={styles.configForm}>
          <div className={styles.formRow}>
            <div className={styles.formGroup}>
              <label className={styles.formLabel}>IMAP Host *</label>
              <input
                type="text"
                placeholder="e.g., imap.gmail.com"
                value={imapHost}
                onChange={(e) => setImapHost(e.target.value)}
                className={styles.formInput}
              />
            </div>
            <div className={styles.formGroup}>
              <label className={styles.formLabel}>IMAP Port</label>
              <input
                type="text"
                placeholder="993"
                value={imapPort}
                onChange={(e) => setImapPort(e.target.value)}
                className={styles.formInput}
              />
            </div>
          </div>
          <div className={styles.formRow}>
            <div className={styles.formGroup}>
              <label className={styles.formLabel}>Email Address *</label>
              <input
                type="text"
                placeholder="your@email.com"
                value={imapUser}
                onChange={(e) => setImapUser(e.target.value)}
                className={styles.formInput}
              />
            </div>
            <div className={styles.formGroup}>
              <label className={styles.formLabel}>Password / App Password *</label>
              <input
                type="password"
                placeholder="Your email password"
                value={imapPass}
                onChange={(e) => setImapPass(e.target.value)}
                className={styles.formInput}
              />
            </div>
          </div>
          <button
            onClick={handleSetConfig}
            disabled={loading || (!imapHost.trim() && !imapUser.trim() && !imapPass.trim())}
            className={`${styles.btn} ${styles.btnPrimary}`}
          >
            {loading ? 'Setting...' : configSet ? 'Update Configuration' : 'Set Configuration'}
          </button>
        </div>
      </div>

      {/* Control Panel */}
      <div className={styles.controlPanel}>
        <div className={styles.controls}>
          <button
            onClick={handleStart}
            disabled={loading || status?.running || !configSet}
            className={`${styles.btn} ${styles.btnPrimary}`}
          >
            {loading ? 'Starting...' : status?.running ? 'Running' : 'Start Monitor'}
          </button>

          <button
            onClick={handleStop}
            disabled={loading || !status?.running}
            className={`${styles.btn} ${styles.btnDanger}`}
          >
            {loading ? 'Stopping...' : 'Stop Monitor'}
          </button>

          <label className={styles.autoRefresh}>
            <input
              type="checkbox"
              checked={autoRefresh}
              onChange={(e) => setAutoRefresh(e.target.checked)}
            />
            <span>Auto-refresh (5s)</span>
          </label>
        </div>

        {/* Status Display */}
        {status && (
          <div className={styles.statusDisplay}>
            <div className={styles.statusGrid}>
              <div className={styles.statusItem}>
                <span className={styles.statusLabel}>Status</span>
                <span className={styles.statusValue}>{status.status}</span>
              </div>
              <div className={styles.statusItem}>
                <span className={styles.statusLabel}>Running</span>
                <span className={styles.statusValue}>{status.running ? 'Yes' : 'No'}</span>
              </div>
              {status.pid && (
                <div className={styles.statusItem}>
                  <span className={styles.statusLabel}>PID</span>
                  <span className={styles.statusValue}>{status.pid}</span>
                </div>
              )}
              {status.connected !== undefined && (
                <div className={styles.statusItem}>
                  <span className={styles.statusLabel}>Connected</span>
                  <span className={styles.statusValue}>{status.connected ? 'Yes' : 'No'}</span>
                </div>
              )}
            </div>
          </div>
        )}
      </div>

      {/* Terminal Output */}
      <div className={styles.terminalSection}>
        <div className={styles.terminalHeader}>
          <h3 className={styles.terminalTitle}>Terminal Output</h3>
          <button
            onClick={fetchOutput}
            className={styles.btn}
          >
            Refresh
          </button>
        </div>
        <pre className={styles.terminalOutput}>
          {output.length > 0 ? output.join('\n') : 'No output yet...'}
        </pre>
      </div>

      {/* Instructions */}
      <div className={styles.instructions}>
        <h3 className={styles.instructionsTitle}>How to Use Email Monitor</h3>
        <ol className={styles.instructionsList}>
          <li><strong>Enable IMAP:</strong> Go to your email settings and enable IMAP access</li>
          <li><strong>Get IMAP Details:</strong> Find your IMAP server address (e.g., imap.gmail.com for Gmail)</li>
          <li><strong>Generate App Password:</strong> For Gmail, generate an app password in Google Account settings</li>
          <li><strong>Enter Configuration:</strong> Fill in the IMAP host, port, email, and password above</li>
          <li><strong>Set Configuration:</strong> Click <strong>Set Configuration</strong> to save your credentials</li>
          <li><strong>Start Monitor:</strong> Click <strong>Start Monitor</strong> button</li>
          <li><strong>Monitor Active:</strong> The system will check for new emails every 30 seconds</li>
          <li><strong>Scam Detection:</strong> Suspicious emails will trigger AI analysis and auto-replies</li>
          <li><strong>Intelligence Collection:</strong> Scam emails will extract intelligence (links, phone numbers, etc.)</li>
          <li><strong>Stop Monitor:</strong> Click <strong>Stop Monitor</strong> when done</li>
        </ol>
        
        <div className={styles.note}>
          <strong>Note:</strong> Your email credentials are encrypted and stored securely in the database. For Gmail, you must use an App Password, not your regular password. The monitor checks for new emails every 30 seconds and automatically responds to scam emails.
        </div>
        
        <div className={styles.securityNote}>
          <strong>⚠️ Security Notice:</strong> Never share your email credentials. Use a dedicated email address for scam monitoring if possible. The system only reads emails and does not delete or modify your inbox.
        </div>
      </div>
    </div>
  );
}
