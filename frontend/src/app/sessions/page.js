"use client";

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import styles from './page.module.css';
import { listSessions, completeSession, deleteSession, deleteCompletedSessions } from '../../lib/api';

export default function SessionsList() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState(null);
  const [notice, setNotice] = useState(null);
  const router = useRouter();

  const refresh = async (after = []) => {
    const res = await listSessions();
    setData(res);
    setLoading(false);
    setBusy(null);
    const err = after.find(r => r && r.error);
    setNotice(err ? `⚠️ ${err.error}` : null);
  };

  useEffect(() => {
    refresh();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const handleComplete = async (sessionId, e) => {
    e.stopPropagation();
    if (!window.confirm(`End session "${sessionId}"? Intelligence will be saved to the Intel Hub.`)) return;
    setBusy(sessionId);
    refresh([await completeSession(sessionId)]);
  };

  const handleDelete = async (sessionId, e) => {
    e.stopPropagation();
    if (!window.confirm(`Permanently delete session "${sessionId}" and its logs?`)) return;
    setBusy(sessionId);
    refresh([await deleteSession(sessionId)]);
  };

  const handleClearCompleted = async () => {
    if (!window.confirm('Delete ALL completed session logs? This cannot be undone.')) return;
    setBusy('all');
    refresh([await deleteCompletedSessions()]);
  };

  if (loading) return <div className={styles.header}>Loading Sessions...</div>;
  if (!data || !data.sessions) return <div className={styles.header}>Error loading sessions.</div>;

  return (
    <div>
      <header className={styles.header}>
        <div className={styles.headerRow}>
          <div>
            <h1 className={styles.title}>Session Logs</h1>
            <p className={styles.subtitle}>View real-time agent transcripts and interactions. Showing {data.returned} of {data.total}.</p>
          </div>
          <div className={styles.headerActions}>
            <button
              className={`${styles.clearBtn} ${busy === 'all' ? styles.disabled : ''}`}
              onClick={handleClearCompleted}
              disabled={busy === 'all'}
            >
              🗑️ Clear Completed Logs
            </button>
          </div>
        </div>
        {notice && <div className={styles.notice}>{notice}</div>}
      </header>

      <div className={styles.tableContainer}>
        {data.sessions.length === 0 ? (
          <div className={styles.empty}>No sessions recorded yet.</div>
        ) : (
          <table className={styles.table}>
            <thead>
              <tr>
                <th>Session ID</th>
                <th>Status</th>
                <th>Scam Confidence</th>
                <th>Turns</th>
                <th>Last Persona</th>
                <th>Last Activity</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {data.sessions.map((item) => {
                const session = item.data;
                const isCompleted = session.completed;
                const confPercent = Math.round(session.confidence * 100);
                const lastActivity = session.last_activity ? new Date(session.last_activity).toLocaleString('en-IN', { 
                  timeZone: 'Asia/Kolkata',
                  year: 'numeric', 
                  month: 'short', 
                  day: 'numeric',
                  hour: '2-digit',
                  minute: '2-digit',
                  hour12: true
                }) : 'N/A';
                const isBusy = busy === item.session_id;

                return (
                  <tr 
                    key={item.session_id} 
                    className={styles.tableRow}
                    onClick={() => router.push(`/sessions/${item.session_id}`)}
                  >
                    <td className={styles.sessionId}>{item.session_id}</td>
                    <td>
                      <span className={`${styles.statusIndicator} ${isCompleted ? styles.statusCompleted : styles.statusActive}`}></span>
                      {isCompleted ? 'Completed' : 'Active'}
                    </td>
                    <td>
                      <span className={`badge ${confPercent > 40 ? 'scam' : 'safe'}`}>
                        {confPercent}% Scam
                      </span>
                    </td>
                    <td>{session.turns}</td>
                    <td>{session.current_persona || 'N/A'}</td>
                    <td>{lastActivity}</td>
                    <td>
                      <div className={styles.actions} onClick={e => e.stopPropagation()}>
                        {!isCompleted && (
                          <button
                            className={`${styles.actionBtn} ${styles.endBtn}`}
                            onClick={e => handleComplete(item.session_id, e)}
                            disabled={isBusy}
                            title="End session and save intelligence to Intel Hub"
                          >
                            {isBusy ? '…' : 'End'}
                          </button>
                        )}
                        <button
                          className={`${styles.actionBtn} ${styles.deleteBtn}`}
                          onClick={e => handleDelete(item.session_id, e)}
                          disabled={isBusy}
                          title="Delete this session log"
                        >
                          🗑️
                        </button>
                      </div>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
}