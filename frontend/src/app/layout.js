import './globals.css';
import styles from './layout.module.css';
import Sidebar from '../components/Sidebar';

export const metadata = {
  title: 'Honey-Pot Admin',
  description: 'Scam Detection & Intelligence Dashboard',
};

export default function RootLayout({ children }) {
  return (
    <html lang="en">
      <body>
        <div className={styles.layoutContainer}>
          <Sidebar />
          <main className={styles.mainContent}>
            {children}
          </main>
        </div>
      </body>
    </html>
  );
}
