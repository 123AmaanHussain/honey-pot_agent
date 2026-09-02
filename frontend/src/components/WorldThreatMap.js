"use client";

import { useState, useEffect, useMemo } from 'react';
import styles from './WorldThreatMap.module.css';
import { getGeoAnalytics } from '../lib/api';

// ─── World projection ────────────────────────────────────────────────────────
// Equirectangular projection matching the SVG viewBox (0 0 800 420).
const VIEW_W = 800;
const VIEW_H = 420;

const project = ([lon, lat]) => [
  ((lon + 180) / 360) * VIEW_W,
  ((90 - lat) / 180) * VIEW_H,
];

// Convert a GeoJSON polygon/multipolygon into an SVG path data string.
function geometryToPath(geometry) {
  const rings = geometry.type === 'Polygon'
    ? geometry.coordinates                       // already a list of rings
    : geometry.coordinates.flat();               // MultiPolygon -> outer rings of each polygon

  let d = '';
  for (const ring of rings) {
    const points = ring.map(([lon, lat]) => {
      const [x, y] = project([lon, lat]);
      return `${x.toFixed(1)},${y.toFixed(1)}`;
    });
    if (points.length >= 3) {
      d += 'M' + points.join('L') + 'Z';
    }
  }
  return d;
}

// ─── Country positions (lat, lon) for tracked threat origins ────────────────
const COUNTRY_CENTROIDS = {
  IN:  ['India',          20.59,  78.96],
  NG:  ['Nigeria',         9.08,   8.68],
  RU:  ['Russia',         61.52, 105.32],
  US:  ['United States',  37.09, -95.71],
  BR:  ['Brazil',        -14.24, -51.93],
  PH:  ['Philippines',    12.88, 121.77],
  VN:  ['Vietnam',        14.06, 108.28],
  ID:  ['Indonesia',      -0.79, 113.92],
  GB:  ['United Kingdom', 55.38,  -3.44],
  CN:  ['China',          35.86, 104.20],
  ZA:  ['South Africa',  -30.56,  22.94],
  BD:  ['Bangladesh',     23.68,  90.36],
  PK:  ['Pakistan',       30.38,  69.35],
  GH:  ['Ghana',           7.95,  -1.02],
  DE:  ['Germany',        51.17,  10.45],
  KE:  ['Kenya',           0.02,  37.90],
  MY:  ['Malaysia',        4.21, 101.98],
  TH:  ['Thailand',       15.87, 100.99],
  MX:  ['Mexico',         23.63, -102.55],
  AU:  ['Australia',     -25.27, 133.78],
  JP:  ['Japan',          36.20, 138.25],
  EG:  ['Egypt',          26.82,  30.80],
  TR:  ['Turkey',         38.96,  35.24],
  FR:  ['France',         46.60,   2.21],
  IT:  ['Italy',          41.87,  12.57],
};

// Fallback blob projections for the 25 tracked countries in case the GeoJSON
// fails to load (kept in the same 0-800 x 0-420 space as preloaded dots).
const FALLBACK_POSITIONS = {
  IN: [62.5, 52.5], NG: [48.0, 55.0], RU: [66.0, 28.0], US: [20.0, 42.0],
  BR: [29.0, 65.0], PH: [76.0, 52.5], VN: [73.5, 50.5], ID: [75.0, 58.5],
  GB: [46.5, 33.0], CN: [70.5, 42.0], ZA: [52.5, 70.0], BD: [65.0, 50.0],
  PK: [61.5, 46.5], GH: [46.5, 54.0], DE: [49.5, 32.0], KE: [54.5, 58.0],
  MY: [73.0, 56.0], TH: [71.5, 51.0], MX: [18.0, 50.0], AU: [78.0, 72.0],
  JP: [79.0, 40.0], EG: [53.5, 47.0], TR: [55.0, 40.5], FR: [47.5, 34.0],
  IT: [50.0, 37.0],
};

// Simple fallback world silhouette (used only if world GeoJSON is unavailable).
const WORLD_PATH = `
M 80 120 L 95 110 L 130 105 L 145 115 L 150 140 L 140 155 L 120 160 L 100 150 Z
M 195 95 L 210 90 L 250 88 L 295 95 L 320 120 L 315 145 L 300 160 L 280 165 L 260 160 L 235 155 L 210 140 L 195 120 Z
M 340 80 L 400 70 L 470 72 L 530 90 L 570 110 L 590 150 L 570 190 L 530 210 L 490 215 L 450 205 L 420 190 L 390 170 L 360 150 L 340 120 Z
M 340 225 L 380 215 L 420 220 L 450 240 L 460 270 L 450 300 L 420 315 L 380 310 L 355 290 L 340 260 Z
M 250 170 L 290 165 L 320 175 L 330 200 L 320 225 L 290 235 L 260 230 L 245 210 Z
M 480 225 L 530 220 L 590 230 L 620 260 L 630 300 L 620 340 L 590 360 L 550 365 L 510 350 L 485 320 L 475 285 L 478 255 Z
M 620 95 L 660 85 L 700 88 L 730 105 L 740 130 L 725 155 L 700 165 L 670 160 L 645 145 L 625 125 Z
M 160 145 L 200 140 L 230 155 L 240 180 L 230 210 L 210 230 L 185 235 L 165 220 L 155 195 L 158 170 Z
`;

const RISK_CONFIG = {
  critical: { color: '#ff4757', glow: 'rgba(255,71,87,0.8)',   label: 'CRITICAL', badge: 'critical' },
  high:     { color: '#ffa502', glow: 'rgba(255,165,2,0.7)',   label: 'HIGH',     badge: 'high'     },
  medium:   { color: '#00d4ff', glow: 'rgba(0,212,255,0.6)',   label: 'MEDIUM',   badge: 'medium'   },
  low:      { color: '#00ff88', glow: 'rgba(0,255,136,0.5)',   label: 'LOW',      badge: 'low'      },
};

const FLAG_EMOJIS = {
  IN:'🇮🇳',NG:'🇳🇬',RU:'🇷🇺',US:'🇺🇸',BR:'🇧🇷',PH:'🇵🇭',VN:'🇻🇳',ID:'🇮🇩',
  GB:'🇬🇧',CN:'🇨🇳',ZA:'🇿🇦',BD:'🇧🇩',PK:'🇵🇰',GH:'🇬🇭',DE:'🇩🇪',KE:'🇰🇪',
  MY:'🇲🇾',TH:'🇹🇭',MX:'🇲🇽',AU:'🇦🇺',JP:'🇯🇵',EG:'🇪🇬',TR:'🇹🇷',FR:'🇫🇷',IT:'🇮🇹',
};

export default function WorldThreatMap() {
  const [geoData, setGeoData] = useState(null);
  const [worldPaths, setWorldPaths] = useState([]);
  const [mapReady, setMapReady] = useState(false);
  const [selected, setSelected]   = useState(null);
  const [hovered, setHovered]     = useState(null);
  const [tooltip, setTooltip]     = useState(null);
  const [filter, setFilter]       = useState('all');
  const [search, setSearch]       = useState('');
  const [pulseTime, setPulseTime] = useState(0);

  // Fetch real world country boundaries
  useEffect(() => {
    let cancelled = false;
    fetch('/world-countries.geojson')
      .then(r => { if (!r.ok) throw new Error(`HTTP ${r.status}`); return r.json(); })
      .then(data => {
        if (cancelled) return;
        const paths = (data.features || [])
          .map(f => geometryToPath(f.geometry))
          .filter(Boolean);
        setWorldPaths(paths);
      })
      .catch(() => { /* fall back to simplified silhouette */ })
      .finally(() => { if (!cancelled) setMapReady(true); });
    return () => { cancelled = true; };
  }, []);

  useEffect(() => {
    getGeoAnalytics().then(d => d && setGeoData(d));
  }, []);

  // Pulse animation ticker
  useEffect(() => {
    const id = setInterval(() => setPulseTime(t => t + 1), 50);
    return () => clearInterval(id);
  }, []);

  const dataByCode = useMemo(() => {
    const map = {};
    for (const d of (geoData?.distribution || [])) map[d.code] = d;
    return map;
  }, [geoData]);

  if (!geoData) {
    return (
      <div className={styles.card}>
        <div className={styles.loading}>
          <div className={styles.loadingSpinner} />
          <span>Loading Threat Intelligence...</span>
        </div>
      </div>
    );
  }

  const distribution = geoData.distribution || [];
  const total_messages = geoData.total_messages || 0;
  const total_scams = geoData.total_scams || 0;

  // Dot position: true centroid on the real map, or fallback % coords otherwise
  const positionOf = (code) => {
    if (mapReady) {
      const c = COUNTRY_CENTROIDS[code];
      if (c) return project([c[2], c[1]]);
    }
    const fb = FALLBACK_POSITIONS[code];
    return fb ? [fb[0] * 8, fb[1] * 4.2] : [0, 0];
  };

  // Max messages for scaling dot size
  const maxMessages = Math.max(...distribution.map(d => d.messages), 1);

  // Filtered leaderboard list
  const filtered = distribution.filter(d => {
    const matchFilter = filter === 'all' || d.risk === filter;
    const matchSearch = !search || d.country.toLowerCase().includes(search.toLowerCase());
    return matchFilter && matchSearch;
  });

  const handleCountryHover = (code, evt) => {
    if (!dataByCode[code]) return;
    setHovered(code);
    setTooltip({ code, x: evt.clientX, y: evt.clientY });
  };

  const handleMouseMove = (evt) => {
    if (tooltip) setTooltip(t => t ? { ...t, x: evt.clientX, y: evt.clientY } : null);
  };

  return (
    <div className={styles.card}>
      {/* Header */}
      <div className={styles.header}>
        <h3 className={styles.title}>
          <span className={styles.titleIcon}>🌐</span>
          Global Threat Origin Map
          <span className={styles.liveTag}>● LIVE</span>
        </h3>
        <div className={styles.headerStats}>
          <div className={styles.headerStat}>
            <span className={styles.headerStatVal}>{total_messages}</span>
            <span className={styles.headerStatLabel}>Total Msgs</span>
          </div>
          <div className={styles.headerStat}>
            <span className={styles.headerStatVal} style={{ color: '#ff4757' }}>{total_scams}</span>
            <span className={styles.headerStatLabel}>Scams</span>
          </div>
          <div className={styles.headerStat}>
            <span className={styles.headerStatVal} style={{ color: '#00d4ff' }}>{distribution.length}</span>
            <span className={styles.headerStatLabel}>Countries</span>
          </div>
        </div>
      </div>

      <div className={styles.body}>
        {/* SVG Map */}
        <div className={styles.mapContainer} onMouseMove={handleMouseMove} onMouseLeave={() => { setHovered(null); setTooltip(null); }}>
          <svg
            viewBox={`0 0 ${VIEW_W} ${VIEW_H}`}
            className={styles.mapSvg}
            preserveAspectRatio="xMidYMid meet"
          >
            {/* Ocean background */}
            <defs>
              <radialGradient id="oceanGrad" cx="50%" cy="50%" r="70%">
                <stop offset="0%" stopColor="#0a1628" />
                <stop offset="100%" stopColor="#04070a" />
              </radialGradient>
              <linearGradient id="landGrad" x1="0" y1="0" x2="0" y2="1">
                <stop offset="0%" stopColor="#16202e" />
                <stop offset="100%" stopColor="#0c121c" />
              </linearGradient>
              <filter id="glow">
                <feGaussianBlur stdDeviation="2" result="coloredBlur" />
                <feMerge><feMergeNode in="coloredBlur" /><feMergeNode in="SourceGraphic" /></feMerge>
              </filter>
            </defs>
            <rect x="0" y="0" width={VIEW_W} height={VIEW_H} fill="url(#oceanGrad)" />

            {/* Latitude/longitude grid lines */}
            {[0.25, 0.5, 0.75].map((f, i) => (
              <g key={i} opacity="0.07">
                <line x1={f * VIEW_W} y1="0" x2={f * VIEW_W} y2={VIEW_H} stroke="#00ff88" strokeWidth="0.5" />
                <line x1="0" y1={f * VIEW_H} x2={VIEW_W} y2={f * VIEW_H} stroke="#00ff88" strokeWidth="0.5" />
              </g>
            ))}

            {/* Real continent outlines (from world-countries.geojson) */}
            {mapReady && worldPaths.length > 0 ? (
              <g fill="url(#landGrad)" stroke="rgba(45,53,66,0.6)" strokeWidth="0.6">
                {worldPaths.map((d, i) => (
                  <path key={i} d={d} />
                ))}
              </g>
            ) : (
              <path d={WORLD_PATH} fill="rgba(20,28,40,0.95)" stroke="rgba(45,53,66,0.6)" strokeWidth="1" />
            )}

            {/* Country threat dots */}
            {Object.keys(COUNTRY_CENTROIDS).map(code => {
              const d = dataByCode[code];
              if (!d) return null;

              const [cx, cy] = positionOf(code);
              const risk = RISK_CONFIG[d.risk] || RISK_CONFIG.low;
              const baseR = 6 + (d.messages / maxMessages) * 20;
              const isHov = hovered === code;
              const isSel = selected === code;

              // Animated pulse rings
              const phase = (pulseTime * 0.04) % 1;
              const pulseR = baseR + phase * 28;
              const pulseOpacity = Math.max(0, 1 - phase) * 0.5;

              return (
                <g key={code} style={{ cursor: 'pointer' }}
                  onClick={() => setSelected(isSel ? null : code)}
                  onMouseEnter={e => handleCountryHover(code, e)}
                  onMouseLeave={() => { setHovered(null); setTooltip(null); }}>
                  {/* Pulse ring */}
                  <circle cx={cx} cy={cy} r={pulseR} fill="none"
                    stroke={risk.color} strokeWidth="1.5"
                    opacity={pulseOpacity}
                    style={{ pointerEvents: 'none' }} />

                  {/* Outer glow */}
                  <circle cx={cx} cy={cy} r={baseR + 4} fill={risk.color} opacity="0.12" />

                  {/* Main dot */}
                  <circle cx={cx} cy={cy} r={isHov || isSel ? baseR + 3 : baseR}
                    fill={risk.color}
                    stroke={isHov || isSel ? '#fff' : 'rgba(255,255,255,0.3)'}
                    strokeWidth={isHov || isSel ? 2 : 1}
                    filter="url(#glow)"
                    style={{ transition: 'r 0.2s ease', filter: `drop-shadow(0 0 ${baseR}px ${risk.color})` }}
                  />

                  {/* Count label */}
                  {(isHov || isSel || d.messages > 20) && (
                    <text x={cx} y={cy + 1} textAnchor="middle" dominantBaseline="central"
                      fill="#fff" fontSize={d.messages > 30 ? 8 : 7} fontWeight="bold"
                      style={{ pointerEvents: 'none', textShadow: '0 0 4px rgba(0,0,0,0.9)' }}>
                      {d.messages}
                    </text>
                  )}

                  {/* Country label on hover */}
                  {(isHov || isSel) && (
                    <text x={cx} y={cy - baseR - 8} textAnchor="middle"
                      fill={risk.color} fontSize="9" fontWeight="bold"
                      style={{ pointerEvents: 'none', filter: `drop-shadow(0 0 4px ${risk.color})` }}>
                      {FLAG_EMOJIS[code]} {d.country}
                    </text>
                  )}
                </g>
              );
            })}
          </svg>

          {/* Tooltip */}
          {tooltip && dataByCode[tooltip.code] && (() => {
            const d = dataByCode[tooltip.code];
            const risk = RISK_CONFIG[d.risk] || RISK_CONFIG.low;
            return (
              <div className={styles.tooltip} style={{ left: tooltip.x + 16, top: tooltip.y - 20 }}>
                <div className={styles.tooltipHeader} style={{ borderColor: risk.color }}>
                  <span>{FLAG_EMOJIS[d.code]}</span>
                  <span>{d.country}</span>
                  <span className={styles.tooltipRisk} style={{ background: risk.color + '22', color: risk.color, borderColor: risk.color }}>
                    {risk.label}
                  </span>
                </div>
                <div className={styles.tooltipRows}>
                  <div className={styles.tooltipRow}><span>📨 Messages</span><b style={{ color: '#00d4ff' }}>{d.messages}</b></div>
                  <div className={styles.tooltipRow}><span>🚨 Scams</span><b style={{ color: '#ff4757' }}>{d.scams}</b></div>
                  <div className={styles.tooltipRow}><span>🎯 Rate</span><b style={{ color: risk.color }}>{Math.round(d.scams / d.messages * 100)}%</b></div>
                </div>
              </div>
            );
          })()}

          {/* Legend */}
          <div className={styles.legend}>
            {Object.entries(RISK_CONFIG).map(([key, cfg]) => (
              <div key={key} className={styles.legendItem}>
                <span className={styles.legendDot} style={{ background: cfg.color, boxShadow: `0 0 6px ${cfg.color}` }} />
                <span className={styles.legendLabel}>{cfg.label}</span>
              </div>
            ))}
          </div>
        </div>

        {/* Leaderboard */}
        <div className={styles.leaderboard}>
          <div className={styles.leaderboardHeader}>
            <span className={styles.leaderboardTitle}>🏆 Country Leaderboard</span>
            <div className={styles.filterRow}>
              <input
                className={styles.searchInput}
                value={search}
                onChange={e => setSearch(e.target.value)}
                placeholder="Search country…"
              />
              <select className={styles.filterSelect} value={filter} onChange={e => setFilter(e.target.value)}>
                <option value="all">All</option>
                <option value="critical">Critical</option>
                <option value="high">High</option>
                <option value="medium">Medium</option>
                <option value="low">Low</option>
              </select>
            </div>
          </div>

          <div className={styles.leaderboardList}>
            {filtered.map((d, i) => {
              const risk = RISK_CONFIG[d.risk] || RISK_CONFIG.low;
              const isActive = selected === d.code || hovered === d.code;
              return (
                <div
                  key={d.code}
                  className={`${styles.leaderboardRow} ${isActive ? styles.leaderboardRowActive : ''}`}
                  style={{ borderLeftColor: risk.color }}
                  onClick={() => setSelected(selected === d.code ? null : d.code)}
                  onMouseEnter={() => setHovered(d.code)}
                  onMouseLeave={() => setHovered(null)}
                >
                  <div className={styles.rowRank} style={{ color: risk.color }}>{i + 1}</div>
                  <div className={styles.rowFlag}>{FLAG_EMOJIS[d.code] || '🌍'}</div>
                  <div className={styles.rowInfo}>
                    <div className={styles.rowName}>{d.country}</div>
                    <div className={styles.rowBar}>
                      <div className={styles.rowBarFill}
                        style={{ width: `${(d.messages / maxMessages) * 100}%`, background: risk.color, boxShadow: `0 0 6px ${risk.color}44` }} />
                    </div>
                  </div>
                  <div className={styles.rowStats}>
                    <span className={styles.rowMsgs} style={{ color: '#00d4ff' }}>{d.messages}</span>
                    <span className={styles.rowRiskBadge} style={{ color: risk.color, borderColor: risk.color + '44', background: risk.color + '11' }}>
                      {risk.label}
                    </span>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      </div>
    </div>
  );
}