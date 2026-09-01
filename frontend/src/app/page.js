import styles from './page.module.css';
import { getMetrics } from '../lib/api';

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

  const { total_sessions, active_sessions, completed_sessions, scams_detected, average_confidence } = metrics;
  const confidencePercent = (average_confidence * 100).toFixed(1);

  return (
    <div className="slide-up scanline-overlay">
      <header className={styles.header}>
        <h1 className={`${styles.title} glitch neon-text`} data-text="🛡️ Command Center">🛡️ Command Center</h1>
        <p className={`${styles.subtitle} typing`}>Cybercrime Detection & Intelligence Operations Center</p>
      </header>

      <div className={styles.grid}>
        <div className={`glass-panel cyber-border ${styles.statCard} pulse-ring`}>
          <div className={styles.statLabel}>Total Engagements</div>
          <div className={`${styles.statValue} neon-text`}>
            {total_sessions}
          </div>
          <div className={styles.statIcon}>🎯</div>
        </div>

        <div className={`glass-panel cyber-border ${styles.statCard} ${styles.dangerCard} holographic`}>
          <div className={styles.statLabel}>Threats Neutralized</div>
          <div className={`${styles.statValue} neon-text`}>
            {scams_detected}
            <span className={styles.statSub}>
              ({total_sessions > 0 ? Math.round((scams_detected / total_sessions) * 100) : 0}%)
            </span>
          </div>
          <div className={styles.statIcon}>🚨</div>
        </div>

        <div className={`glass-panel cyber-border ${styles.statCard} pulse-ring`}>
          <div className={styles.statLabel}>Threat Confidence</div>
          <div className={`${styles.statValue} neon-text`}>
            {confidencePercent}%
          </div>
          <div className={styles.statIcon}>📊</div>
        </div>

        <div className={`glass-panel cyber-border ${styles.statCard} pulse-ring`}>
          <div className={styles.statLabel}>Active / Resolved</div>
          <div className={`${styles.statValue} neon-text`}>
            {active_sessions} <span className={styles.statSub}>/ {completed_sessions}</span>
          </div>
          <div className={styles.statIcon}>⚡</div>
        </div>
      </div>

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
        </div>
        <p style={{ color: 'var(--text-secondary)', marginTop: '1rem' }}>
          All cybercrime detection systems are fully operational. Navigate to Intel Hub for detailed threat analysis and extracted intelligence data.
        </p>
      </section>

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
              <span>Never pay to receive money - legitimate organizations don't ask for upfront payments</span>
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

      <section className={`${styles.section} cyber-grid`}>
        <h2 className={`${styles.sectionTitle} glitch`} data-text="🛡️ Prevention Tips - Stay Safe">🛡️ Prevention Tips - Stay Safe</h2>
        <div className={styles.tipsGrid}>
          <div className={`${styles.tipItem} glass-panel cyber-border`}>
            <span className={`${styles.tipIcon} pulse-ring`}>✅</span>
            <div className={styles.tipContent}>
              <h4 className="neon-text">Verify Identity</h4>
              <p>Always verify the identity of anyone asking for money or personal information through a separate, trusted channel.</p>
            </div>
          </div>
          <div className={`${styles.tipItem} glass-panel cyber-border`}>
            <span className={`${styles.tipIcon} pulse-ring`}>✅</span>
            <div className={styles.tipContent}>
              <h4 className="neon-text">Don't Share Sensitive Data</h4>
              <p>Never share OTPs, passwords, PINs, or bank details with anyone, even if they claim to be from a bank or government agency.</p>
            </div>
          </div>
          <div className={`${styles.tipItem} glass-panel cyber-border`}>
            <span className={`${styles.tipIcon} pulse-ring`}>✅</span>
            <div className={styles.tipContent}>
              <h4 className="neon-text">Be Skeptical of Urgency</h4>
              <p>Scammers create false urgency. Take time to verify - legitimate organizations won't pressure you to act immediately.</p>
            </div>
          </div>
          <div className={`${styles.tipItem} glass-panel cyber-border`}>
            <span className={`${styles.tipIcon} pulse-ring`}>✅</span>
            <div className={styles.tipContent}>
              <h4 className="neon-text">Check URLs Carefully</h4>
              <p>Verify website URLs before entering information. Look for HTTPS and check for slight misspellings or unusual domain names.</p>
            </div>
          </div>
          <div className={`${styles.tipItem} glass-panel cyber-border`}>
            <span className={`${styles.tipIcon} pulse-ring`}>✅</span>
            <div className={styles.tipContent}>
              <h4 className="neon-text">Use Official Channels</h4>
              <p>Contact organizations directly using their official website or phone number (not the one provided in suspicious messages).</p>
            </div>
          </div>
          <div className={`${styles.tipItem} glass-panel cyber-border`}>
            <span className={`${styles.tipIcon} pulse-ring`}>✅</span>
            <div className={styles.tipContent}>
              <h4 className="neon-text">Report Suspicious Activity</h4>
              <p>Report scam attempts to cybercrime.gov.in and your bank. Help protect others by sharing information about scams.</p>
            </div>
          </div>
        </div>
      </section>

      <section className={`${styles.section} cyber-grid`}>
        <h2 className={`${styles.sectionTitle} glitch`} data-text="📚 Educational Resources">📚 Educational Resources</h2>
        <div className={styles.resourcesGrid}>
          <a href="https://www.youtube.com/results?search_query=cybercrime+awareness+india" target="_blank" rel="noopener noreferrer" className={`${styles.resourceCard} glass-panel cyber-border`}>
            <div className={styles.resourceIcon}>🎥</div>
            <h3 className={`${styles.resourceTitle} neon-text`}>Cybercrime Awareness Videos</h3>
            <p className={styles.resourceDescription}>Learn about common scams and how to protect yourself through educational videos.</p>
            <span className={styles.resourceLink}>Watch on YouTube →</span>
          </a>

          <a href="https://cybercrime.gov.in" target="_blank" rel="noopener noreferrer" className={`${styles.resourceCard} glass-panel cyber-border`}>
            <div className={styles.resourceIcon}>🏛️</div>
            <h3 className={`${styles.resourceTitle} neon-text`}>National Cyber Crime Reporting Portal</h3>
            <p className={styles.resourceDescription}>Official Indian government portal for reporting cyber crimes and getting help.</p>
            <span className={styles.resourceLink}>Visit Portal →</span>
          </a>

          <a href="https://www.cert-in.org.in/" target="_blank" rel="noopener noreferrer" className={`${styles.resourceCard} glass-panel cyber-border`}>
            <div className={styles.resourceIcon}>🔒</div>
            <h3 className={`${styles.resourceTitle} neon-text`}>CERT-In (Indian Computer Emergency Response Team)</h3>
            <p className={styles.resourceDescription}>Official government agency for cybersecurity information and alerts.</p>
            <span className={styles.resourceLink}>Learn More →</span>
          </a>

          <a href="https://www.rbi.org.in/" target="_blank" rel="noopener noreferrer" className={`${styles.resourceCard} glass-panel cyber-border`}>
            <div className={styles.resourceIcon}>🏦</div>
            <h3 className={`${styles.resourceTitle} neon-text`}>RBI Consumer Education</h3>
            <p className={styles.resourceDescription}>Reserve Bank of India resources on banking safety and fraud prevention.</p>
            <span className={styles.resourceLink}>Explore Resources →</span>
          </a>
        </div>
      </section>

      <section className={`${styles.section} cyber-grid`}>
        <h2 className={`${styles.sectionTitle} glitch`} data-text="🚨 Report Cybercrime">🚨 Report Cybercrime</h2>
        <div className={`${styles.reportPanel} glass-panel cyber-border`}>
          <div className={styles.reportInfo}>
            <h3 className="neon-text">If you've been a victim of cybercrime:</h3>
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
