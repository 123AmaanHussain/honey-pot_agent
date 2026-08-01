"use client";

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import styles from '../app/layout.module.css';

export default function Sidebar() {
  const pathname = usePathname();

  const links = [
    { href: '/', label: 'Command Center', icon: '�️' },
    { href: '/monitor', label: 'WhatsApp Trap', icon: '📱' },
    { href: '/telegram', label: 'Telegram Trap', icon: '✈️' },
    { href: '/email', label: 'Email Trap', icon: '📧' },
    { href: '/intelligence', label: 'Intel Hub', icon: '🧠' },
    { href: '/sessions', label: 'Session Logs', icon: '�' },
    { href: '/simulator', label: 'Simulator', icon: '🎮' },
  ];

  return (
    <aside className={styles.sidebar}>
      <div className={styles.logo}>
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
