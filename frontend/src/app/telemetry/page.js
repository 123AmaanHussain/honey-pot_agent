"use client";

import { useState, useEffect } from 'react';
import GrafanaDashboard from '../../components/GrafanaDashboard';
import ThreatPieChart from '../../components/ThreatPieChart';
import { getMetrics } from '../../lib/api';
import styles from './page.module.css';

export default function TelemetryPage() {
  const [metrics, setMetrics] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const load = async () => {
      const m = await getMetrics();
      setMetrics(m);
      setLoading(false);
    };
    load();
    const interval = setInterval(load, 10000);
    return () => clearInterval(interval);
  }, []);

  return (
    <div className={`slide-up ${styles.page}`}>
      <header className={styles.header}>
        <div className={styles.headerLeft}>
          <h1 className={`${styles.title} glitch neon-text`} data-text="📡 Ops Telemetry Center">
            📡 Ops Telemetry Center
          </h1>
          <p className={styles.subtitle}>
            Prometheus-backed real-time metrics · Grafana-style panels · Live PromQL queries
          </p>
        </div>
        <div className={styles.headerRight}>
          <div className={styles.statusBadge}>
            <span className={styles.statusDot} />
            <span>Live Monitoring Active</span>
          </div>
        </div>
      </header>

      {loading ? (
        <div className={styles.loading}>
          <div className={styles.spinner} />
          <span>Connecting to Prometheus endpoint…</span>
        </div>
      ) : (
        <>
          <section className={styles.section}>
            <GrafanaDashboard metrics={metrics} />
          </section>

          <section className={styles.section}>
            <ThreatPieChart metrics={metrics} />
          </section>

          <section className={styles.section}>
            <div className={styles.promSetupCard}>
              <h3 className={styles.promTitle}>
                <svg width="20" height="20" viewBox="0 0 40 40" fill="none" style={{ flexShrink: 0 }}>
                  <circle cx="20" cy="20" r="18" stroke="#F46800" strokeWidth="3"/>
                  <circle cx="20" cy="20" r="8" fill="#F46800" opacity="0.8"/>
                </svg>
                Prometheus Setup Guide
              </h3>
              <p className={styles.promDesc}>
                Scrape honeypot metrics directly into your Prometheus instance using the following configuration:
              </p>
              <pre className={styles.promConfig}>{`# prometheus.yml
scrape_configs:
  - job_name: 'honeypot'
    scrape_interval: 15s
    static_configs:
      - targets: ['${process.env.NEXT_PUBLIC_API_URL || 'localhost:8000'}']
    metrics_path: '/metrics/prometheus'`}</pre>

              <h3 className={`${styles.promTitle} ${styles.grafanaTitle}`}>
                <svg width="20" height="20" viewBox="0 0 40 40" fill="none" style={{ flexShrink: 0 }}>
                  <rect width="40" height="40" rx="8" fill="#F46800" opacity="0.2"/>
                  <rect x="8" y="8" width="24" height="24" rx="4" fill="#F46800" opacity="0.6"/>
                </svg>
                Grafana Dashboard Import
              </h3>
              <p className={styles.promDesc}>
                Available metrics to chart in Grafana:
              </p>
              <div className={styles.metricsList}>
                {[
                  ['honeypot_total_sessions', 'Total sessions', 'gauge'],
                  ['honeypot_active_sessions', 'Active sessions', 'gauge'],
                  ['honeypot_scams_detected_total', 'Confirmed scams', 'counter'],
                  ['honeypot_messages_total', 'Total messages processed', 'counter'],
                  ['honeypot_avg_confidence', 'Avg detection confidence', 'gauge'],
                  ['honeypot_uptime_seconds', 'API uptime', 'counter'],
                  ['honeypot_extracted_upi_total', 'Unique UPI IDs extracted', 'gauge'],
                  ['honeypot_extracted_phones_total', 'Unique phone numbers', 'gauge'],
                  ['honeypot_extracted_links_total', 'Phishing links', 'gauge'],
                  ['honeypot_sessions_by_type{scammer_type="..."}', 'Sessions by scammer type', 'gauge'],
                ].map(([metric, desc, type]) => (
                  <div key={metric} className={styles.metricRow}>
                    <code className={styles.metricName}>{metric}</code>
                    <span className={styles.metricDesc}>{desc}</span>
                    <span className={`${styles.metricType} ${styles[`type_${type}`]}`}>{type}</span>
                  </div>
                ))}
              </div>
            </div>
          </section>
        </>
      )}
    </div>
  );
}
