"use client";

import { useState, useEffect, useRef, useCallback } from 'react';
import {
  AreaChart, Area, LineChart, Line, BarChart, Bar,
  XAxis, YAxis, Tooltip, ResponsiveContainer, ReferenceLine
} from 'recharts';
import styles from './GrafanaDashboard.module.css';
import { getTimeseriesMetrics, getPrometheusMetrics } from '../lib/api';

// ─── Time Range Options ──────────────────────────────────────────────────────
const TIME_RANGES = ['5m', '15m', '1h', '6h', '24h', '7d'];
const REFRESH_OPTS = [
  { label: '5s', ms: 5000 },
  { label: '10s', ms: 10000 },
  { label: '30s', ms: 30000 },
  { label: 'Pause', ms: 0 },
];

// ─── Static Gauge Component ──────────────────────────────────────────────────
function RadialGauge({ value, max = 100, label, color = '#00ff88', unit = '' }) {
  const pct = Math.min(value / max, 1);
  const r = 44;
  const circ = 2 * Math.PI * r;
  const dash = pct * circ * 0.75;
  const gap = circ - dash;
  const angle = -135;

  return (
    <div className={styles.gauge}>
      <svg viewBox="0 0 100 100" width="110" height="110">
        <circle cx="50" cy="50" r={r} fill="none" stroke="rgba(45,53,66,0.6)" strokeWidth="8"
          strokeDasharray={`${circ * 0.75} ${circ * 0.25}`}
          strokeDashoffset={circ * 0.125}
          transform="rotate(135 50 50)"
          strokeLinecap="round" />
        <circle cx="50" cy="50" r={r} fill="none" stroke={color} strokeWidth="8"
          strokeDasharray={`${dash} ${gap + circ * 0.25}`}
          strokeDashoffset={circ * 0.125}
          transform="rotate(135 50 50)"
          strokeLinecap="round"
          style={{ filter: `drop-shadow(0 0 6px ${color})`, transition: 'stroke-dasharray 0.6s ease' }}
        />
        <text x="50" y="48" textAnchor="middle" fill={color} fontSize="14" fontWeight="bold">
          {value}{unit}
        </text>
        <text x="50" y="62" textAnchor="middle" fill="#8b949e" fontSize="8">
          / {max}{unit}
        </text>
      </svg>
      <div className={styles.gaugeLabel}>{label}</div>
    </div>
  );
}

// ─── Mini Stat Panel ─────────────────────────────────────────────────────────
function StatPanel({ title, value, unit = '', delta, color = '#00ff88', promql }) {
  return (
    <div className={styles.statPanel}>
      <div className={styles.statPromQL}>{promql}</div>
      <div className={styles.statValue} style={{ color }}>
        {value}<span className={styles.statUnit}>{unit}</span>
      </div>
      <div className={styles.statTitle}>{title}</div>
      {delta !== undefined && (
        <div className={`${styles.statDelta} ${delta >= 0 ? styles.deltaUp : styles.deltaDown}`}>
          {delta >= 0 ? '▲' : '▼'} {Math.abs(delta)}
        </div>
      )}
    </div>
  );
}

// ─── Custom Tooltip ───────────────────────────────────────────────────────────
const CustomTooltip = ({ active, payload, label }) => {
  if (!active || !payload?.length) return null;
  return (
    <div className={styles.tooltip}>
      <div className={styles.tooltipTime}>{label}</div>
      {payload.map((p, i) => (
        <div key={i} className={styles.tooltipRow}>
          <span className={styles.tooltipDot} style={{ background: p.color }} />
          <span className={styles.tooltipName}>{p.name}</span>
          <span className={styles.tooltipVal} style={{ color: p.color }}>{p.value}</span>
        </div>
      ))}
    </div>
  );
};

// ─── Main Component ───────────────────────────────────────────────────────────
export default function GrafanaDashboard({ metrics }) {
  const [timeRange, setTimeRange] = useState('15m');
  const [refreshMs, setRefreshMs] = useState(10000);
  const [series, setSeries] = useState([]);
  const [promRaw, setPromRaw] = useState('');
  const [showPromModal, setShowPromModal] = useState(false);
  const [queryInput, setQueryInput] = useState('honeypot_active_sessions');
  const [queryResult, setQueryResult] = useState(null);
  const [lastRefresh, setLastRefresh] = useState(new Date());
  const [refreshAnim, setRefreshAnim] = useState(false);
  const intervalRef = useRef(null);

  const m = metrics || {};
  const totalSessions   = m.total_sessions   ?? 0;
  const activeSessions  = m.active_sessions  ?? 0;
  const scamsDetected   = m.scams_detected   ?? 0;
  const totalMessages   = m.total_messages   ?? 0;
  const avgConf         = m.average_confidence ?? 0;
  const uptime          = m.uptime_seconds   ?? 0;

  const formatUptime = (s) => {
    if (s < 60) return `${s}s`;
    if (s < 3600) return `${Math.floor(s/60)}m ${s % 60}s`;
    return `${Math.floor(s/3600)}h ${Math.floor((s%3600)/60)}m`;
  };

  const loadData = useCallback(async () => {
    setRefreshAnim(true);
    const ts = await getTimeseriesMetrics();
    if (ts) setSeries(ts);
    setLastRefresh(new Date());
    setTimeout(() => setRefreshAnim(false), 600);
  }, []);

  useEffect(() => {
    loadData();
    if (refreshMs > 0) {
      intervalRef.current = setInterval(loadData, refreshMs);
    }
    return () => clearInterval(intervalRef.current);
  }, [refreshMs, loadData]);

  const handlePromQuery = () => {
    const lines = promRaw.split('\n');
    const matched = lines.filter(l => l.includes(queryInput) && !l.startsWith('#'));
    setQueryResult(matched.length ? matched.join('\n') : `# No results for: ${queryInput}`);
  };

  const loadPromRaw = async () => {
    const raw = await getPrometheusMetrics();
    if (raw) setPromRaw(raw);
    setShowPromModal(true);
  };

  return (
    <div className={styles.wrapper}>
      {/* ── Toolbar ──────────────────────────────────────────────── */}
      <div className={styles.toolbar}>
        <div className={styles.toolbarLeft}>
          <span className={styles.grafanaLogo}>
            <svg width="18" height="18" viewBox="0 0 40 40" fill="none">
              <circle cx="20" cy="20" r="18" stroke="#F46800" strokeWidth="3"/>
              <circle cx="20" cy="20" r="8" fill="#F46800" opacity="0.8"/>
            </svg>
            HoneyPot Ops
          </span>
          <div className={styles.timeRanges}>
            {TIME_RANGES.map(r => (
              <button key={r}
                className={`${styles.rangeBtn} ${timeRange === r ? styles.rangeBtnActive : ''}`}
                onClick={() => setTimeRange(r)}>
                {r}
              </button>
            ))}
          </div>
        </div>
        <div className={styles.toolbarRight}>
          <span className={styles.refreshLabel}>
            <span className={refreshAnim ? styles.refreshSpin : ''}>↺</span>
            {lastRefresh.toLocaleTimeString()}
          </span>
          <div className={styles.refreshOpts}>
            {REFRESH_OPTS.map(o => (
              <button key={o.label}
                className={`${styles.rangeBtn} ${refreshMs === o.ms ? styles.rangeBtnActive : ''}`}
                onClick={() => setRefreshMs(o.ms)}>
                {o.label}
              </button>
            ))}
          </div>
          <button className={styles.promBtn} onClick={loadPromRaw} title="View raw Prometheus metrics">
            <span>📊</span> Prometheus
          </button>
        </div>
      </div>

      {/* ── PromQL Query Bar ─────────────────────────────────────── */}
      <div className={styles.queryBar}>
        <span className={styles.queryIcon}>⊡</span>
        <input
          className={styles.queryInput}
          value={queryInput}
          onChange={e => setQueryInput(e.target.value)}
          placeholder="PromQL: honeypot_active_sessions"
          spellCheck={false}
        />
        <button className={styles.queryBtn} onClick={handlePromQuery}>Run Query ▶</button>
      </div>
      {queryResult && (
        <div className={styles.queryResult}>
          <pre>{queryResult}</pre>
          <button className={styles.closeResult} onClick={() => setQueryResult(null)}>✕</button>
        </div>
      )}

      {/* ── Stat Panels ──────────────────────────────────────────── */}
      <div className={styles.statRow}>
        <StatPanel title="Active Sessions"  value={activeSessions}  color="#00ff88" promql="honeypot_active_sessions" />
        <StatPanel title="Scams Detected"   value={scamsDetected}   color="#ff4757" promql="honeypot_scams_detected_total" />
        <StatPanel title="Messages Total"   value={totalMessages}   color="#00d4ff" promql="honeypot_messages_total" />
        <StatPanel title="Avg Confidence"   value={(avgConf * 100).toFixed(0)} unit="%" color="#ffa502" promql="honeypot_avg_confidence" />
        <StatPanel title="Uptime"           value={formatUptime(Math.floor(uptime))} color="#a55eea" promql="honeypot_uptime_seconds" />
      </div>

      {/* ── Charts Grid ──────────────────────────────────────────── */}
      <div className={styles.chartsGrid}>
        {/* Message Ingestion Rate */}
        <div className={styles.chartPanel}>
          <div className={styles.chartPanelHeader}>
            <span className={styles.chartTitle}>📨 Message Ingestion Rate</span>
            <span className={styles.chartMeta}>{timeRange} · Auto-refresh</span>
          </div>
          <ResponsiveContainer width="100%" height={160}>
            <AreaChart data={series} margin={{ top: 5, right: 10, bottom: 0, left: 0 }}>
              <defs>
                <linearGradient id="msgGrad" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="0%" stopColor="#00d4ff" stopOpacity={0.4} />
                  <stop offset="100%" stopColor="#00d4ff" stopOpacity={0} />
                </linearGradient>
              </defs>
              <XAxis dataKey="time" tick={{ fill: '#6e7681', fontSize: 9 }} tickLine={false} axisLine={false} />
              <YAxis tick={{ fill: '#6e7681', fontSize: 9 }} tickLine={false} axisLine={false} width={28} />
              <Tooltip content={<CustomTooltip />} />
              <Area type="monotone" dataKey="messages" stroke="#00d4ff" strokeWidth={2}
                fill="url(#msgGrad)" name="messages"
                dot={false} activeDot={{ r: 4, fill: '#00d4ff', stroke: '#00d4ff', filter: 'drop-shadow(0 0 6px #00d4ff)' }} />
            </AreaChart>
          </ResponsiveContainer>
        </div>

        {/* Scam Detections */}
        <div className={styles.chartPanel}>
          <div className={styles.chartPanelHeader}>
            <span className={styles.chartTitle}>🚨 Scam Detections</span>
            <span className={styles.chartMeta}>{timeRange}</span>
          </div>
          <ResponsiveContainer width="100%" height={160}>
            <BarChart data={series} margin={{ top: 5, right: 10, bottom: 0, left: 0 }}>
              <defs>
                <linearGradient id="scamGrad" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="0%" stopColor="#ff4757" stopOpacity={0.9} />
                  <stop offset="100%" stopColor="#ff4757" stopOpacity={0.3} />
                </linearGradient>
              </defs>
              <XAxis dataKey="time" tick={{ fill: '#6e7681', fontSize: 9 }} tickLine={false} axisLine={false} />
              <YAxis tick={{ fill: '#6e7681', fontSize: 9 }} tickLine={false} axisLine={false} width={28} />
              <Tooltip content={<CustomTooltip />} />
              <Bar dataKey="scams" fill="url(#scamGrad)" name="scams" radius={[3, 3, 0, 0]}
                style={{ filter: 'drop-shadow(0 0 4px rgba(255,71,87,0.4))' }} />
            </BarChart>
          </ResponsiveContainer>
        </div>

        {/* Gauges */}
        <div className={styles.chartPanel}>
          <div className={styles.chartPanelHeader}>
            <span className={styles.chartTitle}>⚡ System Gauges</span>
          </div>
          <div className={styles.gaugesRow}>
            <RadialGauge value={activeSessions}  max={50}   label="Active Sessions" color="#00ff88" />
            <RadialGauge value={Math.round((1 - avgConf) * 100)} max={100} label="Threat Level" color="#ff4757" unit="%" />
            <RadialGauge value={Math.min(Math.floor(uptime / 60), 999)} max={1440} label="Uptime (min)" color="#00d4ff" />
          </div>
        </div>

        {/* Session Growth */}
        <div className={styles.chartPanel}>
          <div className={styles.chartPanelHeader}>
            <span className={styles.chartTitle}>📈 Session Growth</span>
            <span className={styles.chartMeta}>{timeRange}</span>
          </div>
          <ResponsiveContainer width="100%" height={160}>
            <LineChart data={series} margin={{ top: 5, right: 10, bottom: 0, left: 0 }}>
              <defs>
                <linearGradient id="sessGrad" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="0%" stopColor="#a55eea" stopOpacity={0.4} />
                  <stop offset="100%" stopColor="#a55eea" stopOpacity={0} />
                </linearGradient>
              </defs>
              <XAxis dataKey="time" tick={{ fill: '#6e7681', fontSize: 9 }} tickLine={false} axisLine={false} />
              <YAxis tick={{ fill: '#6e7681', fontSize: 9 }} tickLine={false} axisLine={false} width={28} />
              <Tooltip content={<CustomTooltip />} />
              <Line type="monotone" dataKey="sessions" stroke="#a55eea" strokeWidth={2}
                dot={false} name="sessions"
                activeDot={{ r: 4, fill: '#a55eea', stroke: '#a55eea', filter: 'drop-shadow(0 0 6px #a55eea)' }} />
              <Line type="monotone" dataKey="scams" stroke="#ff4757" strokeWidth={1.5}
                dot={false} name="scams" strokeDasharray="4 2" />
            </LineChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* ── Prometheus Raw Modal ──────────────────────────────────── */}
      {showPromModal && (
        <div className={styles.modalOverlay} onClick={() => setShowPromModal(false)}>
          <div className={styles.modal} onClick={e => e.stopPropagation()}>
            <div className={styles.modalHeader}>
              <span>📊 Prometheus Raw Metrics</span>
              <div className={styles.modalActions}>
                <button className={styles.copyBtn} onClick={() => navigator.clipboard.writeText(promRaw)}>
                  📋 Copy
                </button>
                <button className={styles.closeBtn} onClick={() => setShowPromModal(false)}>✕</button>
              </div>
            </div>
            <div className={styles.modalBody}>
              <pre className={styles.promOutput}>{promRaw || 'Loading…'}</pre>
            </div>
            <div className={styles.modalFooter}>
              <span className={styles.scrapeUrl}>Scrape URL: <code>{process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/metrics/prometheus</code></span>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
