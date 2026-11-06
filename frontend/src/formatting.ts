export function humanize(value: string) { return value.replaceAll('_', ' ').replace(/\b\w/g, c => c.toUpperCase()); }
export function date(value?: string | null) { if (!value) return 'Not recorded'; const parsed = new Date(value); return Number.isNaN(parsed.getTime()) ? value : parsed.toLocaleDateString(undefined, { month: 'short', day: 'numeric', year: 'numeric' }); }
export function initials(name: string) { return name.split(' ').filter(Boolean).map(n => n[0]).slice(0, 2).join(''); }
export function safeUrl(value?: string | null) { if (!value) return undefined; try { const url = new URL(value); return ['https:', 'http:'].includes(url.protocol) ? value : undefined; } catch { return undefined; } }
