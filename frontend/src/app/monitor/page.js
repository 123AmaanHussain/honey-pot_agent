"use client";

import { useState, useEffect } from 'react';
import { startWhatsAppMonitor, stopWhatsAppMonitor, getWhatsAppStatus, getWhatsAppOutput } from '../../lib/api';

export default function MonitorPage() {
  const [status, setStatus] = useState(null);
  const [output, setOutput] = useState([]);
  const [loading, setLoading] = useState(false);
  const [autoRefresh, setAutoRefresh] = useState(true);

  // Fetch status
  const fetchStatus = async () => {
    const result = await getWhatsAppStatus();
    setStatus(result);
  };

  // Fetch output
  const fetchOutput = async () => {
    const result = await getWhatsAppOutput(30);
    if (result.output) {
      setOutput(result.output);
    }
  };

  // Start monitor
  const handleStart = async () => {
    setLoading(true);
    const result = await startWhatsAppMonitor();
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
    const result = await stopWhatsAppMonitor();
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
    fetchStatus();
    fetchOutput();
  }, []);

  return (
    <div style={{ padding: '2rem', maxWidth: '1200px', margin: '0 auto' }}>
      <header style={{ marginBottom: '2rem' }}>
        <h1 style={{ fontSize: '2rem', marginBottom: '0.5rem' }}>📱 WhatsApp Monitor</h1>
        <p style={{ color: 'var(--text-secondary)' }}>
          Control and monitor the WhatsApp scam detection system from here.
        </p>
      </header>

      {/* Control Panel */}
      <div style={{
        background: 'var(--glass-bg)',
        padding: '1.5rem',
        borderRadius: '12px',
        marginBottom: '2rem',
        border: '1px solid var(--border-color)'
      }}>
        <div style={{ display: 'flex', gap: '1rem', alignItems: 'center', flexWrap: 'wrap' }}>
          <button
            onClick={handleStart}
            disabled={loading || status?.running}
            style={{
              padding: '0.75rem 1.5rem',
              background: status?.running ? '#4CAF50' : '#2196F3',
              color: 'white',
              border: 'none',
              borderRadius: '8px',
              cursor: status?.running ? 'not-allowed' : 'pointer',
              opacity: status?.running ? 0.5 : 1,
              fontSize: '1rem',
              fontWeight: '500'
            }}
          >
            {loading ? 'Starting...' : status?.running ? 'Running' : '▶ Start Monitor'}
          </button>

          <button
            onClick={handleStop}
            disabled={loading || !status?.running}
            style={{
              padding: '0.75rem 1.5rem',
              background: '#f44336',
              color: 'white',
              border: 'none',
              borderRadius: '8px',
              cursor: !status?.running ? 'not-allowed' : 'pointer',
              opacity: !status?.running ? 0.5 : 1,
             FontSize: '1rem',
              fontWeight: '500'
            }}
          >
            {loading ? 'Stopping...' : '⏹ Stop Monitor'}
          </button>

          <label style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginLeft: 'auto' }}>
            <input
              type="checkbox"
              checked={autoRefresh}
              onChange={(e) => setAutoRefresh(e.target.checked)}
              style={{ cursor: 'pointer' }}
            />
            <span>Auto-refresh (2s)</span>
          </label>
        </div>

        {/* Status Display */}
        {status && (
          <div style={{ marginTop: '1rem', padding: '1rem', background: 'rgba(0,0,0,0.2)', borderRadius: '8px' }}>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '1rem' }}>
              <div>
                <strong>Status:</strong> {status.status}
              </div>
              <div>
                <strong>Running:</strong> {status.running ? '✅ Yes' : '❌ No'}
              </div>
              {status.pid && (
                <div>
                  <strong>PID:</strong> {status.pid}
                </div>
              )}
              {status.qr_generated !== undefined && (
                <div>
                  <strong>QR Generated:</strong> {status.qr_generated ? '✅ Yes' : '⏳ Waiting'}
                </div>
              )}
              {status.connected !== undefined && (
                <div>
                  <strong>Connected:</strong> {status.connected ? '✅ Yes' : '⏳ No'}
                </div>
              )}
            </div>
          </div>
        )}
      </div>

      {/* QR Code Display */}
      {status?.qr_generated && !status?.connected && (
        <div style={{
          background: 'var(--glass-bg)',
          padding: '2rem',
          borderRadius: '12px',
          marginBottom: '2rem',
          textAlign: 'center',
          border: '1px solid var(--border-color)'
        }}>
          <h2 style={{ marginBottom: '1rem' }}>📷 Scan QR Code with WhatsApp</h2>
          <p style={{ marginBottom: '1rem', color: 'var(--text-secondary)' }}>
            Open WhatsApp → Linked Devices → Link a Device
          </p>
          <div style={{
            background: 'blue',
            padding: '1rem',
            borderRadius: '8px',
            display: 'inline-block'
          }}>
            <pre style={{ fontSize: '8px', lineHeight: '1', margin: 0 }}>
              {output.filter(line => line.includes('█') || line.includes('▄') || line.includes('▀')).join('\n')}
            </pre>
          </div>
        </div>
      )}

      {/* Terminal Output */}
      <div style={{
        background: '#1e1e1e',
        padding: '1.5rem',
        borderRadius: '12px',
        border: '1px solid #333'
      }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
          <h3 style={{ margin: 0, color: '#fff' }}>📋 Terminal Output</h3>
          <button
            onClick={fetchOutput}
            style={{
              padding: '0.5rem 1rem',
              background: '#444',
              color: '#fff',
              border: 'none',
              borderRadius: '4px',
              cursor: 'pointer'
            }}
          >
            🔄 Refresh
          </button>
        </div>
        <pre style={{
          background: '#0d0d0d',
          padding: '1rem',
          borderRadius: '8px',
          color: '#0f0',
          fontSize: '0.85rem',
          maxHeight: '400px',
          overflowY: 'auto',
          margin: 0
        }}>
          {output.length > 0 ? output.join('\n') : 'No output yet...'}
        </pre>
      </div>

      {/* Instructions */}
      <div style={{
        marginTop: '2rem',
        padding: '1.5rem',
        background: 'rgba(33, 150, 243, 0.1)',
        borderRadius: '12px',
        border: '1px solid rgba(33, 150, 243, 0.3)'
      }}>
        <h3 style={{ marginBottom: '1rem' }}>📖 Instructions</h3>
        <ol style={{ marginLeft: '1.5rem', lineHeight: '1.8' }}>
          <li>Click <strong>Start Monitor</strong> to begin the WhatsApp monitor</li>
          <li>Wait for the QR code to appear in the terminal output</li>
          <li>Open WhatsApp on your phone → Settings → Linked Devices → Link a Device</li>
          <li>Scan the QR code displayed above</li>
          <li>Once connected, the monitor will silently watch for scam messages</li>
          <li>Scam messages will trigger automatic AI replies</li>
          <li>Click <strong>Stop Monitor</strong> when done</li>
        </ol>
      </div>
    </div>
  );
}
