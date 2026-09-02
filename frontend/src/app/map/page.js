"use client";

import WorldThreatMap from '../../components/WorldThreatMap';
import styles from './page.module.css';

export default function MapPage() {
  return (
    <div className={`slide-up ${styles.page}`}>
      <header className={styles.header}>
        <h1 className={`${styles.title} glitch neon-text`} data-text="🌐 Global Threat Map">
          🌐 Global Threat Map
        </h1>
        <p className={styles.subtitle}>
          Real-time incoming message origin tracking · Country-level threat intelligence · Interactive radar map
        </p>
      </header>

      <section className={styles.mapSection}>
        <WorldThreatMap />
      </section>

      <section className={styles.infoSection}>
        <div className={styles.infoGrid}>
          <div className={styles.infoCard}>
            <div className={styles.infoIcon}>🛰️</div>
            <h3 className={styles.infoTitle}>Origin Detection</h3>
            <p className={styles.infoText}>
              Incoming message origins are detected using extracted phone number country prefixes
              (+91 → India, +234 → Nigeria, etc.) from intercepted scam conversations.
            </p>
          </div>
          <div className={styles.infoCard}>
            <div className={styles.infoIcon}>🎯</div>
            <h3 className={styles.infoTitle}>Threat Scoring</h3>
            <p className={styles.infoText}>
              Risk levels (Critical/High/Medium/Low) are calculated based on the ratio of confirmed scam sessions
              to total messages originating from each country.
            </p>
          </div>
          <div className={styles.infoCard}>
            <div className={styles.infoIcon}>📡</div>
            <h3 className={styles.infoTitle}>Real-time Updates</h3>
            <p className={styles.infoText}>
              Map data refreshes automatically as new sessions are created and phone numbers
              are extracted from honeypot conversations.
            </p>
          </div>
          <div className={styles.infoCard}>
            <div className={styles.infoIcon}>🔬</div>
            <h3 className={styles.infoTitle}>Intelligence Source</h3>
            <p className={styles.infoText}>
              Country distributions are derived from the /analytics/geo API endpoint which aggregates
              extracted phone prefixes across all active sessions and blends with known threat profiles.
            </p>
          </div>
        </div>
      </section>
    </div>
  );
}
