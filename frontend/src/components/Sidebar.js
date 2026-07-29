"use client";

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import styles from '../app/layout.module.css';

export default function Sidebar() {
  const pathname = usePathname();

  const links = [
    { href: '/', label: 'Overview', icon: '📊' },
    { href: '/monitor', label: 'WhatsApp Monitor', icon: '📱' },
    { href: '/intelligence', label: 'Intelligence Hub', icon: '🧠' },
    { href: '/sessions', label: 'Session Logs', icon: '💬' },
    { href: '/simulator', label: 'Live Simulator', icon: '🎮' },
  ];

  return (
    <aside className={styles.sidebar}>
      <div className={styles.logo}>
        <span>🍯</span>
        <span>Honey<span className={styles.logoAccent}>Pot</span></span>
      </div>
      <nav className={styles.nav}>
        {links.map((link) => (
          <Link 
            key={link.href} 
            href={link.href}
            className={`${styles.navItem} ${pathname === link.href ? styles.active : ''}`}
          >
            <span>{link.icon}</span>
            {link.label}
          </Link>
        ))}
      </nav>
    </aside>
  );
}
