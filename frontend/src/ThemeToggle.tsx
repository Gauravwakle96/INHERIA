import { Moon, Sun } from 'lucide-react';
import { useTheme } from './theme';

export function ThemeToggle() {
  const { theme, toggleTheme } = useTheme();
  const isNight = theme === 'dark';
  const action = isNight ? 'Switch to day mode' : 'Switch to night mode';
  return <button type="button" className="theme-toggle" onClick={toggleTheme} aria-label={action} title={action}>
    {isNight ? <Sun size={16} aria-hidden="true" /> : <Moon size={16} aria-hidden="true" />}
    <span>{isNight ? 'Day' : 'Night'}</span>
  </button>;
}
