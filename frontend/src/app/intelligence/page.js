"use client";

import { useEffect, useState } from 'react';
import jsPDF from 'jspdf';
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
  const [showReport, setShowReport] = useState(false);
  const [selectedSession, setSelectedSession] = useState(null);

  useEffect(() => {
    getIntelligence().then((res) => {
      setData(res);
      setLoading(false);
    });
  }, []);

  if (loading) return <div className={styles.header}>Loading Intelligence...</div>;
  if (!data) return <div className={styles.header}>Error loading data.</div>;

  const intel = data.aggregated_intelligence || {};
  const upis = intel.upiIds || [];
  const phones = intel.phoneNumbers || [];
  const links = intel.phishingLinks || [];
  const banks = intel.bankAccounts || [];
  const sessions = data.sessions_with_intelligence || [];

  // Group intelligence by session
  const intelBySession = sessions.map(session => ({
    session_id: session.session_id,
    scammer_type: session.scammer_type,
    confidence: session.confidence,
    created_at: session.created_at,
    completed: session.completed,
    scammer_profile: session.scammer_profile,
    upiIds: session.extracted?.upiIds || [],
    phoneNumbers: session.extracted?.phoneNumbers || [],
    phishingLinks: session.extracted?.phishingLinks || [],
    bankAccounts: session.extracted?.bankAccounts || [],
    suspiciousKeywords: session.extracted?.suspiciousKeywords || []
  }));

  // Generate professional PDF report for a single session
  const generateSessionPDF = (session) => {
    const doc = new jsPDF();
    const pageWidth = doc.internal.pageSize.getWidth();
    const pageHeight = doc.internal.pageSize.getHeight();
    
    // Colors
    const primaryColor = [56, 189, 248]; // #38BDF8
    const darkColor = [30, 30, 30];
    const lightColor = [245, 245, 245];
    
    // Header with gradient-like background
    doc.setFillColor(...primaryColor);
    doc.rect(0, 0, pageWidth, 50, 'F');
    
    // Honey-Pot Logo placeholder (text-based)
    doc.setTextColor(255, 255, 255);
    doc.setFontSize(24);
    doc.setFont('helvetica', 'bold');
    doc.text('Honey-Pot', 20, 25);
    doc.setFontSize(12);
    doc.setFont('helvetica', 'normal');
    doc.text('Scam Detection System', 20, 35);
    
    // Cybercrime logo placeholder
    doc.setFontSize(10);
    doc.text('Cybercrime Report', pageWidth - 55, 30);
    
    // Report title
    doc.setTextColor(...darkColor);
    doc.setFontSize(18);
    doc.setFont('helvetica', 'bold');
    doc.text('CYBERCRIME COMPLAINT REPORT', pageWidth / 2, 70, { align: 'center' });
    
    // Report metadata
    doc.setFontSize(10);
    doc.setFont('helvetica', 'normal');
    const reportDate = new Date().toLocaleDateString('en-IN', { 
      year: 'numeric', month: 'long', day: 'numeric' 
    });
    doc.text(`Generated: ${reportDate}`, 20, 85);
    doc.text(`Session ID: ${session.session_id}`, 20, 92);
    
    // Section: Scam Details
    doc.setFillColor(...lightColor);
    doc.rect(20, 100, pageWidth - 40, 10, 'F');
    doc.setTextColor(...darkColor);
    doc.setFontSize(12);
    doc.setFont('helvetica', 'bold');
    doc.text('SCAM DETAILS', 25, 107);
    
    doc.setFontSize(10);
    doc.setFont('helvetica', 'normal');
    let yPos = 120;
    doc.text(`Scammer Type: ${session.scammer_type.toUpperCase()}`, 25, yPos);
    yPos += 8;
    doc.text(`Confidence Score: ${(session.confidence * 100).toFixed(0)}%`, 25, yPos);
    yPos += 8;
    doc.text(`Session Date: ${new Date(session.created_at).toLocaleString('en-IN', { 
      timeZone: 'Asia/Kolkata',
      year: 'numeric', 
      month: 'short', 
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit',
      hour12: true
    })}`, 25, yPos);
    yPos += 8;
    
    if (session.scammer_profile) {
      doc.text(`Profile: ${session.scammer_profile}`, 25, yPos);
      yPos += 8;
    }
    
    // Section: Extracted Intelligence
    yPos += 10;
    doc.setFillColor(...lightColor);
    doc.rect(20, yPos, pageWidth - 40, 10, 'F');
    doc.setTextColor(...darkColor);
    doc.setFontSize(12);
    doc.setFont('helvetica', 'bold');
    doc.text('EXTRACTED INTELLIGENCE', 25, yPos + 7);
    yPos += 20;
    
    doc.setFontSize(10);
    doc.setFont('helvetica', 'normal');
    
    if (session.upiIds.length > 0) {
      doc.setTextColor(...primaryColor);
      doc.setFont('helvetica', 'bold');
      doc.text('UPI IDs:', 25, yPos);
      yPos += 7;
      doc.setTextColor(...darkColor);
      doc.setFont('helvetica', 'normal');
      session.upiIds.forEach((upi, i) => {
        doc.text(`  ${i + 1}. ${upi}`, 25, yPos);
        yPos += 6;
      });
      yPos += 5;
    }
    
    if (session.phoneNumbers.length > 0) {
      doc.setTextColor(...primaryColor);
      doc.setFont('helvetica', 'bold');
      doc.text('Phone Numbers:', 25, yPos);
      yPos += 7;
      doc.setTextColor(...darkColor);
      doc.setFont('helvetica', 'normal');
      session.phoneNumbers.forEach((phone, i) => {
        doc.text(`  ${i + 1}. ${phone}`, 25, yPos);
        yPos += 6;
      });
      yPos += 5;
    }
    
    if (session.bankAccounts.length > 0) {
      doc.setTextColor(...primaryColor);
      doc.setFont('helvetica', 'bold');
      doc.text('Bank Accounts:', 25, yPos);
      yPos += 7;
      doc.setTextColor(...darkColor);
      doc.setFont('helvetica', 'normal');
      session.bankAccounts.forEach((bank, i) => {
        doc.text(`  ${i + 1}. ${bank}`, 25, yPos);
        yPos += 6;
      });
      yPos += 5;
    }
    
    if (session.phishingLinks.length > 0) {
      doc.setTextColor(...primaryColor);
      doc.setFont('helvetica', 'bold');
      doc.text('Phishing Links:', 25, yPos);
      yPos += 7;
      doc.setTextColor(...darkColor);
      doc.setFont('helvetica', 'normal');
      session.phishingLinks.forEach((link, i) => {
        doc.text(`  ${i + 1}. ${link}`, 25, yPos);
        yPos += 6;
      });
      yPos += 5;
    }
    
    if (session.suspiciousKeywords.length > 0) {
      doc.setTextColor(...primaryColor);
      doc.setFont('helvetica', 'bold');
      doc.text('Suspicious Keywords:', 25, yPos);
      yPos += 7;
      doc.setTextColor(...darkColor);
      doc.setFont('helvetica', 'normal');
      doc.text(`  ${session.suspiciousKeywords.join(', ')}`, 25, yPos);
      yPos += 10;
    }
    
    // Footer
    doc.setFillColor(...lightColor);
    doc.rect(0, pageHeight - 30, pageWidth, 30, 'F');
    doc.setTextColor(100, 100, 100);
    doc.setFontSize(8);
    doc.setFont('helvetica', 'normal');
    doc.text('This report was generated by Honey-Pot Scam Detection System.', pageWidth / 2, pageHeight - 20, { align: 'center' });
    doc.text('Please verify all information before submitting to authorities.', pageWidth / 2, pageHeight - 12, { align: 'center' });
    
    // Save PDF
    doc.save(`cybercrime_report_${session.session_id}.pdf`);
  };

  // Generate cybercrime complaint link with pre-filled data
  const generateCybercrimeLink = (session) => {
    const baseUrl = 'https://cybercrime.gov.in/login';
    const params = new URLSearchParams();
    
    // Pre-fill common fields (these would need to match the actual form field names)
    if (session.phoneNumbers.length > 0) {
      params.append('victim_mobile', session.phoneNumbers[0]);
    }
    if (session.upiIds.length > 0) {
      params.append('fraud_account', session.upiIds[0]);
    }
    params.append('scam_type', session.scammer_type);
    params.append('description', `Scam detected via Honey-Pot system. Session ID: ${session.session_id}. Scammer Profile: ${session.scammer_profile || 'N/A'}`);
    
    return `${baseUrl}?${params.toString()}`;
  };

  const IntelCard = ({ title, icon, items, sourceMap }) => (
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
              <div className={styles.itemContent}>
                <span className={styles.itemValue}>{item}</span>
                {sourceMap[item] && (
                  <span className={styles.sourceBadge}>
                    From {sourceMap[item].length} session(s)
                  </span>
                )}
              </div>
              <CopyButton text={item} />
            </div>
          ))}
        </div>
      )}
    </div>
  );

  // Create source mapping for each intelligence item
  const createSourceMap = (items, sessions) => {
    const map = {};
    items.forEach(item => {
      map[item] = sessions.filter(s => 
        s.upiIds.includes(item) || 
        s.phoneNumbers.includes(item) || 
        s.bankAccounts.includes(item) ||
        s.phishingLinks.includes(item)
      ).map(s => s.session_id);
    });
    return map;
  };

  const upiSourceMap = createSourceMap(upis, intelBySession);
  const phoneSourceMap = createSourceMap(phones, intelBySession);
  const bankSourceMap = createSourceMap(banks, intelBySession);
  const linkSourceMap = createSourceMap(links, intelBySession);

  return (
    <div className="slide-up">
      <header className={styles.header}>
        <h1 className={styles.title}>🧠 Intel Hub</h1>
        <p className={styles.subtitle}>Aggregated threat intelligence extracted from {sessions.length} engagements.</p>
        <div className={styles.actions}>
          <a 
            href="https://cybercrime.gov.in/login" 
            target="_blank" 
            rel="noopener noreferrer"
            className={styles.cybercrimeBtn}
          >
            🚨 File Cybercrime Report
          </a>
        </div>
      </header>

      <div className={styles.grid}>
        <IntelCard title="UPI IDs" icon="💸" items={upis} sourceMap={upiSourceMap} />
        <IntelCard title="Phone Numbers" icon="📱" items={phones} sourceMap={phoneSourceMap} />
        <IntelCard title="Phishing Links" icon="🔗" items={links} sourceMap={linkSourceMap} />
        <IntelCard title="Bank Accounts" icon="🏦" items={banks} sourceMap={bankSourceMap} />
      </div>

      <div className={styles.sessionsSection}>
        <h2 className={styles.sectionTitle}>📋 Engagement Details & Reports</h2>
        <div className={styles.sessionList}>
          {intelBySession.map((session, idx) => (
            <div key={idx} className={styles.sessionCard}>
              <div className={styles.sessionHeader}>
                <span className={styles.sessionId}>{session.session_id}</span>
                <span className={styles.sessionType}>{session.scammer_type}</span>
                <span className={styles.sessionConfidence}>
                  {(session.confidence * 100).toFixed(0)}% threat confidence
                </span>
                {session.completed && (
                  <span className={styles.completedBadge}>
                    Threat Neutralized
                  </span>
                )}
              </div>
              <div className={styles.sessionDetails}>
                <div>
                  <strong>UPIs:</strong> {session.upiIds.length > 0 ? session.upiIds.join(', ') : 'None'}
                </div>
                <div>
                  <strong>Phones:</strong> {session.phoneNumbers.length > 0 ? session.phoneNumbers.join(', ') : 'None'}
                </div>
                <div>
                  <strong>Banks:</strong> {session.bankAccounts.length > 0 ? session.bankAccounts.join(', ') : 'None'}
                </div>
                <div>
                  <strong>Links:</strong> {session.phishingLinks.length > 0 ? session.phishingLinks.join(', ') : 'None'}
                </div>
                <div className={styles.sessionDate}>
                  {new Date(session.created_at).toLocaleString('en-IN', { 
                    timeZone: 'Asia/Kolkata',
                    year: 'numeric', 
                    month: 'short', 
                    day: 'numeric',
                    hour: '2-digit',
                    minute: '2-digit',
                    second: '2-digit',
                    hour12: true
                  })}
                </div>
              </div>
              <div className={styles.sessionActions}>
                <button 
                  className={styles.pdfBtn}
                  onClick={() => generateSessionPDF(session)}
                >
                  📄 Download Threat Report
                </button>
                <a 
                  href={generateCybercrimeLink(session)}
                  target="_blank"
                  rel="noopener noreferrer"
                  className={styles.complaintBtn}
                >
                  🚨 File Complaint
                </a>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
