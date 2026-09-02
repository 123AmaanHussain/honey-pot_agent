import './globals.css';
import styles from './layout.module.css';
import Sidebar from '../components/Sidebar';
import { ThemeProvider } from '../lib/ThemeContext';
import MatrixRain from '../components/MatrixRain';
import HackerWatermark from '../components/HackerWatermark';
import CyberEffects from '../components/CyberEffects';

export const metadata = {
  title: 'Honey-Pot Admin',
  description: 'Scam Detection & Intelligence Dashboard',
};

export default function RootLayout({ children }) {
  return (
    <html lang="en">
      <body>
        <ThemeProvider>
          <HackerWatermark />
          <MatrixRain />
          <CyberEffects />
          <div className={styles.layoutContainer}>
            <Sidebar />
            <main className={styles.mainContent}>
              {children}
            </main>
          </div>
        </ThemeProvider>
      </body>
    </html>
  );
}
