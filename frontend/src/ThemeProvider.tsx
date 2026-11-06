import { useEffect, useLayoutEffect, useState, type ReactNode } from 'react';
import { ThemeContext, type Theme } from './theme';

export function ThemeProvider({ children }: { children: ReactNode }) {
  const [theme, setTheme] = useState<Theme>(() =>
    document.documentElement.dataset.theme === 'light' ? 'light' : 'dark',
  );

  useLayoutEffect(() => {
    document.documentElement.dataset.theme = theme;
    document.documentElement.style.colorScheme = theme;
    document.querySelector('meta[name="theme-color"]')?.setAttribute(
      'content', theme === 'dark' ? '#0b1019' : '#f4f7fb',
    );
    try {
      localStorage.setItem('inheria-theme', theme);
    } catch {
      // Theme switching still works when browser storage is unavailable.
    }
  }, [theme]);

  useEffect(() => {
    function syncPreference(event: StorageEvent) {
      if (event.key !== 'inheria-theme') return;
      if (event.newValue === 'light' || event.newValue === 'dark') {
        setTheme(event.newValue);
      }
    }
    window.addEventListener('storage', syncPreference);
    return () => window.removeEventListener('storage', syncPreference);
  }, []);

  return <ThemeContext.Provider value={{ theme, toggleTheme: () => setTheme(current => current === 'dark' ? 'light' : 'dark') }}>{children}</ThemeContext.Provider>;
}
