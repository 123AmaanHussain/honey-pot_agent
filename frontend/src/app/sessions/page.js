"use client";

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import styles from './page.module.css';
import { listSessions } from '../../lib/api';

export default function SessionsList() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const router = useRouter();

  useEffect(() => {
    listSessions().then((res) => {
      setData(res);
      setLoading(false);
    });
  }, []);

  if (loading) return <div className={styles.header}>Loading Sessions...</div>;
  if (!data || !data.sessions) return <div className={styles.header}>Error loading sessions.</div>;

  return (
    <div>
      <header className={styles.header}>
        <h1 className={styles.title}>Session Logs</h1>
        <p className={styles.subtitle}>View real-time agent transcripts and interactions. Showing {data.returned} of {data.total}.</p>
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
              </tr>
            </thead>
            <tbody>
              {data.sessions.map((item) => {
                const session = item.data;
                const isCompleted = session.completed;
                const confPercent = Math.round(session.confidence * 100);
                
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
