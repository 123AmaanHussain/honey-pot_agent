"use client";

import { useEffect, useState, use } from 'react';
import Link from 'next/link';
import styles from './page.module.css';
import { getSession } from '../../../lib/api';

export default function SessionDetail({ params }) {
  const unwrappedParams = use(params);
  const sessionId = unwrappedParams.id;
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    getSession(sessionId).then((res) => {
      setData(res);
      setLoading(false);
    });
  }, [sessionId]);

  if (loading) return <div className={styles.header}>Loading Session {sessionId}...</div>;
  if (!data) return <div className={styles.header}>Error loading session. It may not exist.</div>;

  const session = data.data;
  const messages = data.messages || [];
  const confPercent = Math.round(session.confidence * 100);

  return (
    <div>
      <div className={styles.header}>
        <div>
          <Link href="/sessions" className={styles.backBtn}>← Back to Sessions</Link>
          <h1 className={styles.title}>Session Details</h1>
          <div className={styles.sessionId}>{sessionId}</div>
        </div>
        <div className={`badge ${confPercent > 40 ? 'scam' : 'safe'}`}>
          {confPercent}% Scam Confidence
        </div>
      </div>

      <div className={styles.content}>
        {/* Chat Transcript */}
        <div className={styles.chatWindow}>
          <div className={styles.chatHeader}>
            Transcript
            <span style={{ fontSize: '0.875rem', fontWeight: 'normal', color: 'var(--text-secondary)' }}>
              {messages.length} messages
            </span>
          </div>
          <div className={styles.chatMessages}>
            {messages.length === 0 ? (
              <div style={{ color: 'var(--text-secondary)', textAlign: 'center' }}>No messages in this session.</div>
            ) : (
              messages.map((msg, idx) => (
                <div key={idx} className={`${styles.message} ${msg.sender === 'scammer' ? styles.scammerMsg : styles.agentMsg}`}>
                  <div className={styles.msgRole}>{msg.sender === 'scammer' ? 'Suspicious Actor' : 'Honey-Pot Agent'}</div>
                  <div>{msg.text}</div>
                </div>
              ))
            )}
          </div>
        </div>

        {/* Details Panel */}
        <div className={styles.detailsPanel}>
          <div className={styles.panel}>
            <h2 className={styles.panelTitle}>Session State</h2>
            <div className={styles.metricRow}>
              <span className={styles.metricLabel}>Status</span>
              <span>{session.completed ? 'Completed / Escaped' : 'Active'}</span>
            </div>
            <div className={styles.metricRow}>
              <span className={styles.metricLabel}>Turns</span>
              <span>{session.turns}</span>
            </div>
            <div className={styles.metricRow}>
              <span className={styles.metricLabel}>Current Persona</span>
              <span>{session.current_persona || 'N/A'}</span>
            </div>
            <div className={styles.metricRow}>
              <span className={styles.metricLabel}>Created</span>
              <span>{session.created_at ? new Date(session.created_at).toLocaleString('en-IN', { 
                timeZone: 'Asia/Kolkata',
                year: 'numeric', 
                month: 'short', 
                day: 'numeric',
                hour: '2-digit',
                minute: '2-digit',
                hour12: true
              }) : 'N/A'}</span>
            </div>
            <div className={styles.metricRow}>
              <span className={styles.metricLabel}>Last Activity</span>
              <span>{session.last_activity ? new Date(session.last_activity).toLocaleString('en-IN', { 
                timeZone: 'Asia/Kolkata',
                year: 'numeric', 
                month: 'short', 
                day: 'numeric',
                hour: '2-digit',
                minute: '2-digit',
                hour12: true
              }) : 'N/A'}</span>
            </div>
          </div>

          <div className={styles.panel}>
            <h2 className={styles.panelTitle}>Extracted Intelligence</h2>
            {Object.entries(session.extracted).map(([key, items]) => {
              if (!items || items.length === 0) return null;
              return (
                <div key={key} style={{ marginBottom: '1rem' }}>
                  <div className={styles.metricLabel} style={{ textTransform: 'capitalize', marginBottom: '0.5rem' }}>
                    {key.replace('_', ' ')}
                  </div>
                  {items.map((item, idx) => (
                    <div key={idx} className={styles.intelItem}>{item}</div>
                  ))}
                </div>
              );
            })}
            
            {Object.values(session.extracted).every(arr => !arr || arr.length === 0) && (
              <div style={{ color: 'var(--text-secondary)', fontStyle: 'italic', fontSize: '0.875rem' }}>
                No intelligence extracted yet.
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
