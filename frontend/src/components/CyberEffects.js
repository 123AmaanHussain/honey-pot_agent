'use client';

import { useEffect, useState } from 'react';

export default function CyberEffects() {
  const [randomBinary, setRandomBinary] = useState('');

  useEffect(() => {
    // Generate random binary stream
    const generateBinary = () => {
      const binary = Array(50).fill(0).map(() => Math.random() > 0.5 ? '1' : '0').join('');
      setRandomBinary(binary);
    };

    // Update binary every 100ms
    const interval = setInterval(generateBinary, 100);

    return () => clearInterval(interval);
  }, []);

  return (
    <>
      {/* Random Binary Stream */}
      <div style={{
        position: 'fixed',
        top: '10px',
        right: '10px',
        fontFamily: 'monospace',
        fontSize: '10px',
        color: 'rgba(0, 255, 136, 0.3)',
        zIndex: 1000,
        pointerEvents: 'none',
        whiteSpace: 'nowrap',
      }}>
        {randomBinary}
      </div>

      {/* Corner Decorations */}
      <div style={{
        position: 'fixed',
        top: '0',
        left: '0',
        width: '50px',
        height: '50px',
        borderTop: '2px solid var(--color-green)',
        borderLeft: '2px solid var(--color-green)',
        opacity: 0.3,
        zIndex: 1000,
        pointerEvents: 'none',
      }} />

      <div style={{
        position: 'fixed',
        top: '0',
        right: '0',
        width: '50px',
        height: '50px',
        borderTop: '2px solid var(--color-green)',
        borderRight: '2px solid var(--color-green)',
        opacity: 0.3,
        zIndex: 1000,
        pointerEvents: 'none',
      }} />

      <div style={{
        position: 'fixed',
        bottom: '0',
        left: '0',
        width: '50px',
        height: '50px',
        borderBottom: '2px solid var(--color-green)',
        borderLeft: '2px solid var(--color-green)',
        opacity: 0.3,
        zIndex: 1000,
        pointerEvents: 'none',
      }} />

      <div style={{
        position: 'fixed',
        bottom: '0',
        right: '0',
        width: '50px',
        height: '50px',
        borderBottom: '2px solid var(--color-green)',
        borderRight: '2px solid var(--color-green)',
        opacity: 0.3,
        zIndex: 1000,
        pointerEvents: 'none',
      }} />

      {/* Random Glitch Text */}
      <div style={{
        position: 'fixed',
        bottom: '20px',
        left: '20px',
        fontFamily: 'monospace',
        fontSize: '10px',
        color: 'rgba(0, 255, 136, 0.2)',
        zIndex: 1000,
        pointerEvents: 'none',
      }}>
        SYSTEM_STATUS: OPERATIONAL
      </div>

      <div style={{
        position: 'fixed',
        bottom: '20px',
        right: '20px',
        fontFamily: 'monospace',
        fontSize: '10px',
        color: 'rgba(0, 255, 136, 0.2)',
        zIndex: 1000,
        pointerEvents: 'none',
      }}>
        THREAT_LEVEL: LOW
      </div>
    </>
  );
}
