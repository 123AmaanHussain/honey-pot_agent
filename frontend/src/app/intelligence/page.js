"use client";

import { useEffect, useState } from 'react';
import styles from './page.module.css';
import { getIntelligence } from '../../lib/api';

const CopyButton = ({ text }) => {
  const [copied, setCopied] = useState(false);

  const handleCopy = () => {
    navigator.clipboard.writeText(text);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <button className={styles.copyBtn} onClick={handleCopy}>
      {copied ? 'Copied!' : 'Copy'}
    </button>
  );
};

export default function IntelligenceHub() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    getIntelligence().then((res) => {
      setData(res);
      setLoading(false);
    });
  }, []);

  if (loading) return <div className={styles.header}>Loading Intelligence...</div>;
  if (!data) return <div className={styles.header}>Error loading data.</div>;

  const intel = data.aggregated_intelligence || {};
  const upis = intel.upi_ids || [];
  const phones = intel.phone_numbers || [];
  const links = intel.links || [];
  const banks = intel.bank_accounts || [];

  const IntelCard = ({ title, icon, items }) => (
    <div className={`glass-panel ${styles.card}`}>
      <div className={styles.cardHeader}>
        <div className={styles.cardTitle}>
          <span>{icon}</span> {title}
        </div>
        <span className={styles.count}>{items.length}</span>
      </div>
      
      {items.length === 0 ? (
        <div className={styles.empty}>No {title.toLowerCase()} extracted yet.</div>
      ) : (
        <div className={styles.list}>
          {items.map((item, idx) => (
            <div key={idx} className={styles.listItem}>
              <span>{item}</span>
              <CopyButton text={item} />
            </div>
          ))}
        </div>
      )}
    </div>
  );

  return (
    <div>
      <header className={styles.header}>
        <h1 className={styles.title}>Intelligence Hub</h1>
        <p className={styles.subtitle}>Aggregated threat data extracted from {data.sessions_with_intelligence?.length || 0} sessions.</p>
      </header>

      <div className={styles.grid}>
        <IntelCard title="UPI IDs" icon="💸" items={upis} />
        <IntelCard title="Phone Numbers" icon="📱" items={phones} />
        <IntelCard title="Phishing Links" icon="🔗" items={links} />
        <IntelCard title="Bank Accounts" icon="🏦" items={banks} />
      </div>
    </div>
  );
}
