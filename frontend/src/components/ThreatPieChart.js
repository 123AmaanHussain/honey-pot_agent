"use client";

import { useState, useEffect } from 'react';
import {
  PieChart, Pie, Cell, Tooltip, Legend, ResponsiveContainer, Sector
} from 'recharts';
import styles from './ThreatPieChart.module.css';

// ─── Data Definitions ───────────────────────────────────────────────────────

const SCAM_TACTICS = [
  { name: 'Investment Scheme', value: 31, color: '#ff4757', icon: '📈' },
  { name: 'UPI Payment Fraud', value: 26, color: '#ff6b35', icon: '💰' },
  { name: 'Impersonation',     value: 19, color: '#ffa502', icon: '🎭' },
  { name: 'Crypto Scam',       value: 14, color: '#a55eea', icon: '🪙' },
  { name: 'Phishing Email',    value: 7,  color: '#00d4ff', icon: '📧' },
  { name: 'Fake Job Offer',    value: 3,  color: '#00ff88', icon: '💼' },
];

const PLATFORM_CHANNELS = [
  { name: 'WhatsApp Trap',  value: 45, color: '#25D366', icon: '📱' },
  { name: 'Telegram Bot',   value: 32, color: '#0088cc', icon: '✈️' },
  { name: 'Email Trap',     value: 15, color: '#ff4757', icon: '📧' },
  { name: 'Webhook API',    value: 8,  color: '#ffa502', icon: '🔗' },
];

const SEVERITY_VERDICTS = [
  { name: 'Critical Malicious',  value: 38, color: '#ff4757', icon: '🚨' },
  { name: 'Neutralized',         value: 29, color: '#ff6b35', icon: '⚡' },
  { name: 'High Risk Suspicious',value: 21, color: '#ffa502', icon: '⚠️' },
  { name: 'Legitimate Pass-thru',value: 12, color: '#00ff88', icon: '✅' },
];

const TABS = [
  { id: 'tactics',   label: 'Scam Tactics',   data: SCAM_TACTICS },
  { id: 'channels',  label: 'Inbound Channels', data: PLATFORM_CHANNELS },
  { id: 'verdicts',  label: 'Threat Verdicts',  data: SEVERITY_VERDICTS },
];

// ─── Custom Label ────────────────────────────────────────────────────────────
const renderCustomLabel = ({ cx, cy, midAngle, innerRadius, outerRadius, percent }) => {
  if (percent < 0.06) return null;
  const RADIAN = Math.PI / 180;
  const r = innerRadius + (outerRadius - innerRadius) * 0.55;
  const x = cx + r * Math.cos(-midAngle * RADIAN);
  const y = cy + r * Math.sin(-midAngle * RADIAN);
  return (
    <text x={x} y={y} fill="#fff" textAnchor="middle" dominantBaseline="central"
      fontSize={11} fontWeight="bold" style={{ textShadow: '0 0 6px rgba(0,0,0,0.8)' }}>
      {`${(percent * 100).toFixed(0)}%`}
    </text>
  );
};

// ─── Active Shape (hover pullout) ────────────────────────────────────────────
const renderActiveShape = (props) => {
  const { cx, cy, innerRadius, outerRadius, startAngle, endAngle,
          fill, payload, percent, value } = props;
  return (
    <g>
      <Sector cx={cx} cy={cy} innerRadius={innerRadius - 4} outerRadius={outerRadius + 12}
        startAngle={startAngle} endAngle={endAngle} fill={fill}
        style={{ filter: `drop-shadow(0 0 12px ${fill})` }} />
      <Sector cx={cx} cy={cy} innerRadius={outerRadius + 14} outerRadius={outerRadius + 18}
        startAngle={startAngle} endAngle={endAngle} fill={fill} />
      <text x={cx} y={cy - 10} textAnchor="middle" fill="#fff" fontSize={13} fontWeight="bold">
        {payload.icon} {payload.name}
      </text>
      <text x={cx} y={cy + 12} textAnchor="middle" fill={fill} fontSize={18} fontWeight="bold">
        {value}%
      </text>
      <text x={cx} y={cy + 32} textAnchor="middle" fill="#8b949e" fontSize={11}>
        {(percent * 100).toFixed(1)}% of total
      </text>
    </g>
  );
};

// ─── Custom Tooltip ───────────────────────────────────────────────────────────
const CustomTooltip = ({ active, payload }) => {
  if (!active || !payload?.length) return null;
  const d = payload[0];
  return (
    <div className={styles.tooltip}>
      <div className={styles.tooltipHeader} style={{ borderColor: d.payload.color }}>
        <span>{d.payload.icon}</span>
        <span>{d.name}</span>
      </div>
      <div className={styles.tooltipBody}>
        <span className={styles.tooltipValue} style={{ color: d.payload.color }}>{d.value}%</span>
        <span className={styles.tooltipLabel}>share of threats</span>
      </div>
    </div>
  );
};

// ─── Main Component ───────────────────────────────────────────────────────────
export default function ThreatPieChart({ metrics }) {
  const [activeTab, setActiveTab] = useState(0);
  const [activeIndex, setActiveIndex] = useState(null);
  const [animKey, setAnimKey] = useState(0);

  const tab = TABS[activeTab];
  const data = tab.data;

  const total = data.reduce((sum, d) => sum + d.value, 0);

  const handleTabChange = (idx) => {
    setActiveTab(idx);
    setActiveIndex(null);
    setAnimKey(k => k + 1);
  };

  return (
    <div className={styles.card}>
      <div className={styles.header}>
        <h3 className={styles.title}>
          <span className={styles.titleIcon}>🎯</span>
          Threat Distribution
        </h3>
        <div className={styles.tabs}>
          {TABS.map((t, i) => (
            <button
              key={t.id}
              className={`${styles.tab} ${i === activeTab ? styles.tabActive : ''}`}
              onClick={() => handleTabChange(i)}
            >
              {t.label}
            </button>
          ))}
        </div>
      </div>

      <div className={styles.body}>
        {/* Chart */}
        <div className={styles.chartArea}>
          <ResponsiveContainer width="100%" height={280}>
            <PieChart key={animKey}>
              <defs>
                {data.map((d, i) => (
                  <radialGradient key={i} id={`grad-${i}`} cx="50%" cy="50%" r="50%">
                    <stop offset="0%" stopColor={d.color} stopOpacity={0.9} />
                    <stop offset="100%" stopColor={d.color} stopOpacity={0.5} />
                  </radialGradient>
                ))}
              </defs>
              <Pie
                data={data}
                cx="50%" cy="50%"
                innerRadius={70} outerRadius={110}
                dataKey="value"
                activeIndex={activeIndex}
                activeShape={renderActiveShape}
                labelLine={false}
                label={activeIndex === null ? renderCustomLabel : null}
                animationBegin={0}
                animationDuration={700}
                onMouseEnter={(_, index) => setActiveIndex(index)}
                onMouseLeave={() => setActiveIndex(null)}
              >
                {data.map((entry, index) => (
                  <Cell
                    key={index}
                    fill={`url(#grad-${index})`}
                    stroke={entry.color}
                    strokeWidth={1}
                    style={{ cursor: 'pointer', outline: 'none' }}
                  />
                ))}
              </Pie>
              <Tooltip content={<CustomTooltip />} />
            </PieChart>
          </ResponsiveContainer>

          {/* Center text when no slice is hovered */}
          {activeIndex === null && (
            <div className={styles.centerText}>
              <span className={styles.centerValue}>{data.length}</span>
              <span className={styles.centerLabel}>categories</span>
            </div>
          )}
        </div>

        {/* Legend */}
        <div className={styles.legend}>
          {data.map((d, i) => (
            <div
              key={i}
              className={`${styles.legendItem} ${i === activeIndex ? styles.legendActive : ''}`}
              onMouseEnter={() => setActiveIndex(i)}
              onMouseLeave={() => setActiveIndex(null)}
            >
              <div className={styles.legendDot} style={{ background: d.color, boxShadow: `0 0 8px ${d.color}` }} />
              <span className={styles.legendName}>{d.icon} {d.name}</span>
              <div className={styles.legendBar}>
                <div
                  className={styles.legendFill}
                  style={{ width: `${d.value}%`, background: d.color, boxShadow: `0 0 6px ${d.color}66` }}
                />
              </div>
              <span className={styles.legendPct} style={{ color: d.color }}>{d.value}%</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
