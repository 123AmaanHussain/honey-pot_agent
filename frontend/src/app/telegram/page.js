"use client";

import { useState, useEffect } from 'react';
import { getTelegramTokenStatus, setTelegramToken, startTelegramMonitor, stopTelegramMonitor, getTelegramStatus, getTelegramOutput } from '../../lib/api';
import styles from './page.module.css';

export default function TelegramMonitorPage() {
  const [status, setStatus] = useState(null);
  const [output, setOutput] = useState([]);
  const [loading, setLoading] = useState(false);
  const [autoRefresh, setAutoRefresh] = useState(true);
  const [botToken, setBotToken] = useState('');
  const [tokenSet, setTokenSet] = useState(false);

  // Fetch status
  const fetchStatus = async () => {
    const result = await getTelegramStatus();
    setStatus(result);
  };

  // Fetch output
  const fetchOutput = async () => {
    const result = await getTelegramOutput(30);
    if (result.output) {
      setOutput(result.output);
    }
  };

  // Check if token is already set
  const checkTokenStatus = async () => {
    const result = await getTelegramTokenStatus();
    if (result.token_set) {
      setTokenSet(true);
    }
  };

  // Set bot token
  const handleSetToken = async () => {
    if (!botToken.trim()) {
      alert('Please enter a bot token');
      return;
    }
    setLoading(true);
    const result = await setTelegramToken(botToken);
    setLoading(false);
    if (result.error) {
      alert(`Error: ${result.error}`);
    } else {
      setTokenSet(true);
      alert('Bot token set successfully');
    }
  };

  // Start monitor
  const handleStart = async () => {
    if (!tokenSet) {
      alert('Please set the bot token first');
      return;
    }
    setLoading(true);
    const result = await startTelegramMonitor();
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
    const result = await stopTelegramMonitor();
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
    checkTokenStatus();
    fetchStatus();
    fetchOutput();
  }, []);

  return (
    <div className="slide-up">
      <header className={styles.header}>
        <h1 className={styles.title}>Telegram Monitor</h1>
        <p className={styles.subtitle}>
          Control and monitor the Telegram scam detection system from here.
        </p>
      </header>

      {/* Bot Token Input */}
      <div className={styles.tokenSection}>
        <h2 className={styles.tokenTitle}>
          {tokenSet ? 'Telegram Bot Token (Already Set)' : 'Enter Telegram Bot Token'}
        </h2>
        <p className={styles.tokenDescription}>
          {tokenSet 
            ? 'Your bot token is saved. You can start the monitor directly or update the token if needed.'
            : 'To use the Telegram monitor, you need a bot token from BotFather.'
          }
        </p>
        <div className={styles.tokenInput}>
          <input
            type="text"
            placeholder={tokenSet ? 'Token is set (enter new token to update)' : 'Enter your bot token (e.g., 123456789:ABCdefGHIjklMNOpqrsTUVwxyz)'}
            value={botToken}
            onChange={(e) => setBotToken(e.target.value)}
            className={styles.tokenField}
          />
          <button
            onClick={handleSetToken}
            disabled={loading || (!botToken.trim() && !tokenSet)}
            className={`${styles.btn} ${styles.btnPrimary}`}
          >
            {loading ? 'Setting...' : tokenSet ? 'Update Token' : 'Set Token'}
          </button>
        </div>
      </div>

      {/* Control Panel */}
      <div className={styles.controlPanel}>
        <div className={styles.controls}>
          <button
            onClick={handleStart}
            disabled={loading || status?.running || !tokenSet}
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
        <h3 className={styles.instructionsTitle}>How to Use Telegram Monitor</h3>
        <ol className={styles.instructionsList}>
          <li><strong>Create a Telegram Bot:</strong> Open Telegram and search for <code>@BotFather</code></li>
          <li><strong>Create New Bot:</strong> Send <code>/newbot</code> command and follow the prompts</li>
          <li><strong>Get Token:</strong> BotFather will provide you with a bot token (format: <code>123456789:ABCdefGHIjklMNOpqrsTUVwxyz</code>)</li>
          <li><strong>Enter Token:</strong> Paste your bot token in the input field above and click <strong>Set Token</strong></li>
          <li><strong>Start Monitor:</strong> Click <strong>Start Monitor</strong> button</li>
          <li><strong>Monitor Active:</strong> The bot will listen for scam messages and automatically respond</li>
          <li><strong>Intelligence Collection:</strong> Scam messages will trigger AI responses and extract intelligence</li>
          <li><strong>Stop Monitor:</strong> Click <strong>Stop Monitor</strong> when done</li>
        </ol>
        
        <div className={styles.note}>
          <strong>Note:</strong> Your bot token is saved securely in the database. You only need to enter it once. The token will persist across server restarts.
        </div>
      </div>
    </div>
  );
}
