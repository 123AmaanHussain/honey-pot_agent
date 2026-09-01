'use client';

import { useTheme } from '../lib/ThemeContext';

export default function ThemeToggle() {
  const { theme, toggleTheme } = useTheme();

  return (
    <button
      onClick={toggleTheme}
      className="btn btn-cyberpunk"
      style={{
        padding: '0.5rem 1rem',
        fontSize: '12px',
        display: 'flex',
        alignItems: 'center',
        gap: '0.5rem',
      }}
    >
      {theme === 'dark' ? '☀️ LIGHT MODE' : '🌙 DARK MODE'}
    </button>
  );
}
