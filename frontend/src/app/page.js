import styles from './page.module.css';
import Link from 'next/link';
import { getMetrics } from '../lib/api';
import ThreatPieChart from '../components/ThreatPieChart';
import WorldThreatMap from '../components/WorldThreatMap';

export default async function Dashboard() {
  const metrics = await getMetrics();

  if (!metrics) {
    return (
      <div className={styles.header}>
        <h1 className={styles.title}>🛡️ Command Center</h1>
        <p className={styles.subtitle}>⚠️ System Offline - API Connection Failed</p>
      </div>
    );
  }

  const { total_sessions, active_sessions, completed_sessions, scams_detected, average_confidence, total_messages, uptime_seconds } = metrics;
  const confidencePercent = (average_confidence * 100).toFixed(1);
  const scamRate = total_sessions > 0 ? Math.round((scams_detected / total_sessions) * 100) : 0;
  const uptimeHours = Math.floor((uptime_seconds || 0) / 3600);
  const uptimeMins  = Math.floor(((uptime_seconds || 0) % 3600) / 60);

  return (
    <div className={`slide-up scanline-overlay ${styles.page}`}>
      <header className={styles.header}>
        <h1 className={`${styles.title} glitch neon-text`} data-text="🛡️ Command Center">🛡️ Command Center</h1>
        <p className={`${styles.subtitle} typing`}>Cybercrime Detection &amp; Intelligence Operations Center</p>
      </header>

      {/* ── Stat Cards ────────────────────────────────────────────── */}
      <div className={styles.grid}>
        <div className={`glass-panel cyber-border ${styles.statCard} pulse-ring`}>
          <div className={styles.statLabel}>Total Engagements</div>
          <div className={`${styles.statValue} neon-text`}>{total_sessions}</div>
          <div className={styles.statIcon}>🎯</div>
        </div>

        <div className={`glass-panel cyber-border ${styles.statCard} ${styles.dangerCard} holographic`}>
          <div className={styles.statLabel}>Threats Neutralized</div>
          <div className={`${styles.statValue} neon-text`}>
            {scams_detected}
            <span className={styles.statSub}>({scamRate}%)</span>
          </div>
          <div className={styles.statIcon}>🚨</div>
        </div>

        <div className={`glass-panel cyber-border ${styles.statCard} pulse-ring`}>
          <div className={styles.statLabel}>Threat Confidence</div>
          <div className={`${styles.statValue} neon-text`}>{confidencePercent}%</div>
          <div className={styles.statIcon}>📊</div>
        </div>

        <div className={`glass-panel cyber-border ${styles.statCard} pulse-ring`}>
          <div className={styles.statLabel}>Active / Resolved</div>
          <div className={`${styles.statValue} neon-text`}>
            {active_sessions} <span className={styles.statSub}>/ {completed_sessions}</span>
          </div>
          <div className={styles.statIcon}>⚡</div>
        </div>

        <div className={`glass-panel cyber-border ${styles.statCard} pulse-ring`}>
          <div className={styles.statLabel}>Messages Processed</div>
          <div className={`${styles.statValue} neon-text`}>{total_messages ?? 0}</div>
          <div className={styles.statIcon}>💬</div>
        </div>

        <div className={`glass-panel cyber-border ${styles.statCard} pulse-ring`}>
          <div className={styles.statLabel}>System Uptime</div>
          <div className={`${styles.statValue} neon-text`} style={{ fontSize: '1.4rem' }}>
            {uptimeHours}h {uptimeMins}m
          </div>
          <div className={styles.statIcon}>⏱️</div>
        </div>
      </div>

      {/* ── Grafana/Prometheus Quick Panel ────────────────────────── */}
      <section className={styles.section}>
        <div className={styles.grafanaWidget}>
          <div className={styles.grafanaWidgetLeft}>
            <div className={styles.grafanaLogo}>
              <svg width="22" height="22" viewBox="0 0 40 40" fill="none">
                <circle cx="20" cy="20" r="18" stroke="#F46800" strokeWidth="3"/>
                <circle cx="20" cy="20" r="8" fill="#F46800" opacity="0.8"/>
              </svg>
              <span>Prometheus · Grafana</span>
            </div>
            <p className={styles.grafanaDesc}>
              Real-time Prometheus metrics scraping with Grafana-style panels, PromQL query inspector, 
              live timeseries charts, and system health gauges.
            </p>
          </div>
          <div className={styles.grafanaWidgetRight}>
            <div className={styles.promMetrics}>
              <div className={styles.promMetric}>
                <code>honeypot_active_sessions</code>
                <span style={{ color: '#00ff88' }}>{active_sessions}</span>
              </div>
              <div className={styles.promMetric}>
                <code>honeypot_scams_detected_total</code>
                <span style={{ color: '#ff4757' }}>{scams_detected}</span>
              </div>
              <div className={styles.promMetric}>
                <code>honeypot_avg_confidence</code>
                <span style={{ color: '#ffa502' }}>{average_confidence}</span>
              </div>
            </div>
            <Link href="/telemetry" className={styles.grafanaLink}>
              Open Telemetry Center →
            </Link>
          </div>
        </div>
      </section>

      {/* ── World Threat Map ──────────────────────────────────────── */}
      <section className={styles.section}>
        <h2 className={`${styles.sectionTitle} glitch`} data-text="🌐 Global Threat Origin Map">🌐 Global Threat Origin Map</h2>
        <WorldThreatMap />
        <div className={styles.sectionFooter}>
          <Link href="/map" className={styles.viewFullLink}>View Full Screen Map →</Link>
        </div>
      </section>

      {/* ── Threat Distribution Pie Charts ────────────────────────── */}
      <section className={styles.section}>
        <h2 className={`${styles.sectionTitle} glitch`} data-text="🎯 Threat Distribution Analytics">🎯 Threat Distribution Analytics</h2>
        <ThreatPieChart metrics={metrics} />
        <div className={styles.sectionFooter}>
          <Link href="/telemetry" className={styles.viewFullLink}>View Full Telemetry Dashboard →</Link>
        </div>
      </section>

      {/* ── System Status ─────────────────────────────────────────── */}
      <section className={`${styles.section} cyber-grid`}>
        <h2 className={`${styles.sectionTitle} glitch`} data-text="🛡️ System Status">🛡️ System Status</h2>
        <div className={styles.statusPanel}>
          <div className={styles.statusItem}>
            <span className={`${styles.statusDot} pulse-ring`}></span>
            <span className={`${styles.statusText} neon-text`}>Honey-Pot Core: OPERATIONAL</span>
          </div>
          <div className={styles.statusItem}>
            <span className={`${styles.statusDot} pulse-ring`}></span>
            <span className={`${styles.statusText} neon-text`}>Neural Network: ACTIVE</span>
          </div>
          <div className={styles.statusItem}>
            <span className={`${styles.statusDot} pulse-ring`}></span>
            <span className={`${styles.statusText} neon-text`}>Database: CONNECTED</span>
          </div>
          <div className={styles.statusItem}>
            <span className={`${styles.statusDot} pulse-ring`}></span>
            <span className={`${styles.statusText} neon-text`}>Threat Intelligence: MONITORING</span>
          </div>
          <div className={styles.statusItem}>
            <span className={`${styles.statusDot} pulse-ring`}></span>
            <span className={`${styles.statusText} neon-text`} style={{ color: '#F46800' }}>Prometheus: SCRAPING</span>
          </div>
          <div className={styles.statusItem}>
            <span className={`${styles.statusDot} pulse-ring`}></span>
            <span className={`${styles.statusText} neon-text`} style={{ color: '#F46800' }}>Geo Analytics: ACTIVE</span>
          </div>
        </div>
      </section>

      {/* ── Common Scam Tactics ───────────────────────────────────── */}
      <section className={`${styles.section} cyber-grid`}>
        <h2 className={`${styles.sectionTitle} glitch`} data-text="⚠️ Common Scam Tactics - How You Get Trapped">⚠️ Common Scam Tactics - How You Get Trapped</h2>
        <div className={styles.tacticsGrid}>
          <div className={`${styles.tacticCard} glass-panel cyber-border`}>
            <div className={styles.tacticIcon}>📱</div>
            <h3 className={`${styles.tacticTitle} neon-text`}>WhatsApp Investment Scams</h3>
            <p className={styles.tacticDescription}>
              Scammers send messages claiming to be from friends or family, asking for urgent financial help or promoting fake investment schemes with guaranteed returns.
            </p>
            <div className={styles.tacticWarning}>
              <span className={styles.warningIcon}>⚠️</span>
              <span>Always verify identity through another channel before sending money</span>
            </div>
          </div>

          <div className={`${styles.tacticCard} glass-panel cyber-border`}>
            <div className={styles.tacticIcon}>✈️</div>
            <h3 className={`${styles.tacticTitle} neon-text`}>Telegram Crypto Scams</h3>
            <p className={styles.tacticDescription}>
              Fake crypto trading groups promise unrealistic returns. Scammers use social proof, fake testimonials, and pressure tactics to make you invest quickly.
            </p>
            <div className={styles.tacticWarning}>
              <span className={styles.warningIcon}>⚠️</span>
              <span>Legitimate investments never guarantee returns or pressure you to act fast</span>
            </div>
          </div>

          <div className={`${styles.tacticCard} glass-panel cyber-border`}>
            <div className={styles.tacticIcon}>📧</div>
            <h3 className={`${styles.tacticTitle} neon-text`}>Phishing Email Attacks</h3>
            <p className={styles.tacticDescription}>
              Emails impersonating banks, government agencies, or companies asking for sensitive information, account verification, or payment details.
            </p>
            <div className={styles.tacticWarning}>
              <span className={styles.warningIcon}>⚠️</span>
              <span>Never click links in unsolicited emails - verify directly with the organization</span>
            </div>
          </div>

          <div className={`${styles.tacticCard} glass-panel cyber-border`}>
            <div className={styles.tacticIcon}>💰</div>
            <h3 className={`${styles.tacticTitle} neon-text`}>UPI Payment Frauds</h3>
            <p className={styles.tacticDescription}>
              Scammers request UPI payments for fake services, lottery winnings, or emergency situations. They often use fake payment screenshots and urgency.
            </p>
            <div className={styles.tacticWarning}>
              <span className={styles.warningIcon}>⚠️</span>
              <span>Never pay to receive money - legitimate organizations don&apos;t ask for upfront payments</span>
            </div>
          </div>

          <div className={`${styles.tacticCard} glass-panel cyber-border`}>
            <div className={styles.tacticIcon}>🎭</div>
            <h3 className={`${styles.tacticTitle} neon-text`}>Impersonation Scams</h3>
            <p className={styles.tacticDescription}>
              Scammers pose as government officials, police, bank employees, or tech support to threaten legal action or demand immediate payment.
            </p>
            <div className={styles.tacticWarning}>
              <span className={styles.warningIcon}>⚠️</span>
              <span>Government agencies never demand payment via phone, WhatsApp, or UPI</span>
            </div>
          </div>

          <div className={`${styles.tacticCard} glass-panel cyber-border`}>
            <div className={styles.tacticIcon}>🔗</div>
            <h3 className={`${styles.tacticTitle} neon-text`}>Fake Job Offers</h3>
            <p className={styles.tacticDescription}>
              Too-good-to-be-true job offers with high salaries for minimal work. Scammers ask for registration fees, training costs, or equipment payments.
            </p>
            <div className={styles.tacticWarning}>
              <span className={styles.warningIcon}>⚠️</span>
              <span>Legitimate employers never ask candidates to pay for job opportunities</span>
            </div>
          </div>
        </div>
      </section>

      {/* ── Report ────────────────────────────────────────────────── */}
      <section className={`${styles.section} cyber-grid`}>
        <h2 className={`${styles.sectionTitle} glitch`} data-text="🚨 Report Cybercrime">🚨 Report Cybercrime</h2>
        <div className={`${styles.reportPanel} glass-panel cyber-border`}>
          <div className={styles.reportInfo}>
            <h3 className="neon-text">If you&apos;ve been a victim of cybercrime:</h3>
            <ul className={styles.reportList}>
              <li>📞 Call the National Cyber Crime Helpline: <strong>1930</strong></li>
              <li>🌐 File a complaint online: <a href="https://cybercrime.gov.in" target="_blank" rel="noopener noreferrer" className={styles.reportLink}>cybercrime.gov.in</a></li>
              <li>📱 Use the Cyber Crime Reporting App available on Android and iOS</li>
              <li>🏦 Contact your bank immediately to freeze accounts if financial fraud occurred</li>
              <li>📸 Save all evidence: screenshots, messages, call logs, transaction details</li>
            </ul>
          </div>
          <div className={styles.reportActions}>
            <a href="https://cybercrime.gov.in" target="_blank" rel="noopener noreferrer" className={`${styles.reportButton} btn-cyberpunk`}>
              🚨 File Complaint Now
            </a>
            <a href="tel:1930" className={`${styles.reportButtonSecondary} btn-cyberpunk`}>
              📞 Call 1930
            </a>
          </div>
        </div>
      </section>
    </div>
  );
}
