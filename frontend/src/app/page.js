import styles from './page.module.css';
import { getMetrics } from '../lib/api';

export default async function Dashboard() {
  const metrics = await getMetrics();

  if (!metrics) {
    return (
      <div className={styles.header}>
        <h1 className={styles.title}>System Overview</h1>
        <p className={styles.subtitle}>Error loading metrics. Is the API running?</p>
      </div>
    );
  }

  const { total_sessions, active_sessions, completed_sessions, scams_detected, average_confidence } = metrics;
  const confidencePercent = (average_confidence * 100).toFixed(1);

  return (
    <div>
      <header className={styles.header}>
        <h1 className={styles.title}>System Overview</h1>
        <p className={styles.subtitle}>Real-time monitoring of Honey-Pot agent interactions.</p>
      </header>

      <div className={styles.grid}>
        <div className={`glass-panel ${styles.statCard} ${styles.safe}`}>
          <div className={styles.statLabel}>Total Sessions</div>
          <div className={styles.statValue}>
            {total_sessions}
          </div>
        </div>

        <div className={`glass-panel ${styles.statCard} ${styles.scam}`}>
          <div className={styles.statLabel}>Scams Detected</div>
          <div className={styles.statValue}>
            {scams_detected}
            <span className={styles.statSub}>
              ({total_sessions > 0 ? Math.round((scams_detected / total_sessions) * 100) : 0}%)
            </span>
          </div>
        </div>

        <div className={`glass-panel ${styles.statCard}`}>
          <div className={styles.statLabel}>Avg Scam Confidence</div>
          <div className={styles.statValue}>
            {confidencePercent}%
          </div>
        </div>

        <div className={`glass-panel ${styles.statCard}`}>
          <div className={styles.statLabel}>Active / Completed</div>
          <div className={styles.statValue}>
            {active_sessions} <span className={styles.statSub}>/ {completed_sessions}</span>
          </div>
        </div>
      </div>

      <section className={styles.section}>
        <h2 className={styles.sectionTitle}><span>⚡</span> System Status</h2>
        <p style={{ color: 'var(--text-secondary)' }}>
          Honey-Pot Core API and Database persistence are currently fully operational.
          To view detailed data extracts (UPIs, phone numbers, links), navigate to the Intelligence Hub.
        </p>
      </section>
    </div>
  );
}
