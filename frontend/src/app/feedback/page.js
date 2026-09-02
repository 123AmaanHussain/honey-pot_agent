"use client";

import { useState, useEffect } from 'react';
import { getFeedbackStats, getFeedbackCorrections, submitFeedback } from '@/lib/api';
import styles from './page.module.css';

export default function FeedbackPage() {
  const [stats, setStats] = useState(null);
  const [corrections, setCorrections] = useState([]);
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [message, setMessage] = useState('');
  const [correctionType, setCorrectionType] = useState('fp');
  const [category, setCategory] = useState('');
  const [notes, setNotes] = useState('');
  const [result, setResult] = useState(null);

  useEffect(() => {
    loadData();
  }, []);

  async function loadData() {
    setLoading(true);
    const [s, c] = await Promise.all([getFeedbackStats(), getFeedbackCorrections()]);
    setStats(s);
    setCorrections(c?.corrections || []);
    setLoading(false);
  }

  async function handleSubmit(e) {
    e.preventDefault();
    if (!message.trim()) return;
    setSubmitting(true);
    setResult(null);
    try {
      const res = await submitFeedback({
        message: message.trim(),
        correctionType,
        originalPrediction: correctionType === 'fp',
        actualLabel: correctionType === 'fp',
        category,
        notes,
      });
      setResult({ type: 'success', text: res.message });
      setMessage(''); setCategory(''); setNotes('');
      loadData();
    } catch (err) {
      setResult({ type: 'error', text: err.message });
    }
    setSubmitting(false);
  }

  if (loading) return <div className={styles.loading}>Loading self-learning data...</div>;

  return (
    <div className={styles.container}>
      <header className={styles.header}>
        <h1 className={styles.title}>SELF-LEARNING LAYER</h1>
        <p className={styles.subtitle}>
          Every human correction makes the system permanently smarter.
          Mark false positives and false negatives to train the detection engine.
        </p>
      </header>

      {/* Stats Cards */}
      {stats && (
        <div className={styles.statsGrid}>
          <div className={styles.statCard}>
            <div className={styles.statValue}>{stats.total_corrections}</div>
            <div className={styles.statLabel}>Total Corrections</div>
          </div>
          <div className={`${styles.statCard} ${styles.fp}`}>
            <div className={styles.statValue}>{stats.false_positives_corrected}</div>
            <div className={styles.statLabel}>False Positives Fixed</div>
          </div>
          <div className={`${styles.statCard} ${styles.fn}`}>
            <div className={styles.statValue}>{stats.false_negatives_corrected}</div>
            <div className={styles.statLabel}>False Negatives Fixed</div>
          </div>
          <div className={`${styles.statCard} ${styles.pattern}`}>
            <div className={styles.statValue}>{stats.patterns_extracted}</div>
            <div className={styles.statLabel}>Patterns Learned</div>
          </div>
        </div>
      )}

      {/* How it works */}
      <div className={styles.howItWorks}>
        <h2 className={styles.sectionTitle}>How Self-Learning Works</h2>
        <div className={styles.pipeline}>
          <div className={styles.pipelineStep}>
            <div className={styles.stepNumber}>1</div>
            <div className={styles.stepContent}>
              <strong>FP Cache</strong>
              <p>Corrected messages are stored. If the same message appears again, the system skips the LLM and returns the correct answer instantly.</p>
            </div>
          </div>
          <div className={styles.pipelineStep}>
            <div className={styles.stepNumber}>2</div>
            <div className={styles.stepContent}>
              <strong>Few-Shot Injection</strong>
              <p>Past corrections are injected into the LLM prompt as examples. The model sees &quot;don&apos;t make this mistake again&quot; before every analysis.</p>
            </div>
          </div>
          <div className={styles.pipelineStep}>
            <div className={styles.stepNumber}>3</div>
            <div className={styles.stepContent}>
              <strong>Pattern Extraction</strong>
              <p>When 3+ false positives share the same category or keyword, a rule is automatically created to reduce scam scores for similar messages.</p>
            </div>
          </div>
        </div>
      </div>

      {/* Submit Correction Form */}
      <div className={styles.formSection}>
        <h2 className={styles.sectionTitle}>Submit Correction</h2>
        <form onSubmit={handleSubmit} className={styles.form}>
          <div className={styles.formGroup}>
            <label>Message Text</label>
            <textarea
              className={styles.textarea}
              value={message}
              onChange={(e) => setMessage(e.target.value)}
              placeholder="Paste the message that was misclassified..."
              rows={3}
              required
            />
          </div>
          <div className={styles.formRow}>
            <div className={styles.formGroup}>
              <label>Correction Type</label>
              <select value={correctionType} onChange={(e) => setCorrectionType(e.target.value)} className={styles.select}>
                <option value="fp">False Positive (flagged as scam, was legit)</option>
                <option value="fn">False Negative (missed scam, was actually scam)</option>
              </select>
            </div>
            <div className={styles.formGroup}>
              <label>Category (optional)</label>
              <input
                className={styles.input}
                value={category}
                onChange={(e) => setCategory(e.target.value)}
                placeholder="e.g. bank_alert, otp, personal"
              />
            </div>
          </div>
          <div className={styles.formGroup}>
            <label>Notes (optional)</label>
            <input
              className={styles.input}
              value={notes}
              onChange={(e) => setNotes(e.target.value)}
              placeholder="Why was this misclassified?"
            />
          </div>
          <button type="submit" className={styles.submitBtn} disabled={submitting || !message.trim()}>
            {submitting ? 'Submitting...' : 'Submit Correction'}
          </button>
        </form>
        {result && (
          <div className={result.type === 'success' ? styles.success : styles.error}>
            {result.text}
          </div>
        )}
      </div>

      {/* Corrections Log */}
      <div className={styles.logSection}>
        <h2 className={styles.sectionTitle}>Recent Corrections ({corrections.length})</h2>
        {corrections.length === 0 ? (
          <p className={styles.empty}>No corrections yet. Submit one above to start training the system.</p>
        ) : (
          <div className={styles.tableWrapper}>
            <table className={styles.table}>
              <thead>
                <tr>
                  <th>Type</th>
                  <th>Message</th>
                  <th>Category</th>
                  <th>Notes</th>
                  <th>Timestamp</th>
                </tr>
              </thead>
              <tbody>
                {[...corrections].reverse().map((c) => (
                  <tr key={c.id}>
                    <td>
                      <span className={c.correction_type === 'fp' ? styles.badgeFp : styles.badgeFn}>
                        {c.correction_type.toUpperCase()}
                      </span>
                    </td>
                    <td className={styles.msgCell}>{c.message?.slice(0, 80)}...</td>
                    <td>{c.category || '-'}</td>
                    <td>{c.notes || '-'}</td>
                    <td className={styles.tsCell}>{c.timestamp?.slice(0, 19).replace('T', ' ')}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}
