import { useEffect, useRef, type ButtonHTMLAttributes, type ReactNode } from 'react';
import { AlertCircle, ArrowRight, CheckCheck, ChevronRight, FileText, LoaderCircle, ShieldCheck, X } from 'lucide-react';
import { ApiError } from './api';
import type { Citation } from './types';
import { humanize, date, safeUrl } from './formatting';

export function Button({ children, className = '', variant = 'primary', busy = false, ...props }: ButtonHTMLAttributes<HTMLButtonElement> & { variant?: 'primary' | 'secondary' | 'ghost' | 'danger'; busy?: boolean }) {
  return <button className={`button button-${variant} ${className}`} {...props} disabled={props.disabled || busy}>{busy ? <LoaderCircle size={16} className="spin" aria-hidden="true" /> : null}{children}</button>;
}
export function Badge({ value }: { value: string }) { return <span className={`badge status-${value.toLowerCase().replaceAll(' ', '_')}`}><span aria-hidden="true" />{humanize(value)}</span>; }
export function Panel({ children, title, description, action, className = '' }: { children: ReactNode; title?: string; description?: string; action?: ReactNode; className?: string }) {
  return <section className={`panel ${className}`}>{title && <header className="panel-heading"><div><h2>{title}</h2>{description && <p>{description}</p>}</div>{action}</header>}{children}</section>;
}
export function PageHeader({ eyebrow = 'Knowledge continuity', title, description, action }: { eyebrow?: string; title: string; description: string; action?: ReactNode }) {
  useEffect(() => { document.title = `${title} · INHERIA`; }, [title]);
  return <header className="page-heading"><div><div className="eyebrow">{eyebrow}</div><h1>{title}</h1><p>{description}</p></div>{action && <div className="page-actions">{action}</div>}</header>;
}
export function Empty({ title, description, action }: { title: string; description: string; action?: ReactNode }) { return <div className="empty"><div className="empty-icon"><FileText size={25} /></div><h3>{title}</h3><p>{description}</p>{action}</div>; }
export function Loading({ label = 'Loading authorised project knowledge…' }: { label?: string }) { return <div className="loading" role="status"><LoaderCircle className="spin" size={20} /><span>{label}</span><div className="skeleton-lines"><i /><i /><i /></div></div>; }
export function ErrorState({ error, retry }: { error: Error; retry?: () => void }) { const forbidden = error instanceof ApiError && error.status === 403; return <div className="notice notice-error" role="alert"><AlertCircle size={19} /><div><strong>{forbidden ? 'Permission required' : 'Unable to complete this request'}</strong><p>{error.message}</p>{error instanceof ApiError && error.requestId && <small>Request {error.requestId}</small>}{retry && <Button variant="secondary" onClick={retry}>Try again</Button>}</div></div>; }
export function Notice({ children, tone = 'info' }: { children: ReactNode; tone?: 'info' | 'warning' | 'success' }) { return <div className={`notice notice-${tone}`}><ShieldCheck size={18} /><div>{children}</div></div>; }
export function EvidenceButton({ citations, onClick }: { citations: Citation[]; onClick: () => void }) { return <button className="evidence-button" onClick={onClick}><ShieldCheck size={14} />{citations.length ? `${citations.length} evidence ${citations.length === 1 ? 'source' : 'references'}` : 'Insufficient evidence'}<ChevronRight size={14} /></button>; }
export function CitationList({ citations, openSource }: { citations: Citation[]; openSource?: (sourceId: string) => void }) {
  return citations.length ? <div className="citation-list">{citations.map((item, index) => <article className="citation" key={`${item.id}-${index}`}><div className="citation-top"><span className="source-number">{index + 1}</span><div><strong>{item.source_name}</strong><small>{item.locator} · v{item.source_version} · {date(item.source_time)}</small></div>{item.synthetic && <span className="mini-label">Demo</span>}</div><blockquote>{item.quote}</blockquote><div className="citation-actions">{openSource && <Button variant="ghost" onClick={() => openSource(item.source_id)}>Open source <ArrowRight size={14} /></Button>}{safeUrl(item.source_url) && <a href={safeUrl(item.source_url)} target="_blank" rel="noopener noreferrer">Original source ↗</a>}</div></article>)}</div> : <Empty title="Insufficient evidence" description="This item has no accessible supporting citations. It cannot be treated as verified knowledge." />;
}
export function Dialog({ open, title, children, onClose, wide = false }: { open: boolean; title: string; children: ReactNode; onClose: () => void; wide?: boolean }) {
  const ref = useRef<HTMLDialogElement>(null);
  useEffect(() => { const dialog = ref.current; if (!dialog) return; if (open && !dialog.open) dialog.showModal(); if (!open && dialog.open) dialog.close(); }, [open]);
  return <dialog ref={ref} className={`dialog ${wide ? 'dialog-wide' : ''}`} onCancel={onClose} onClick={event => { if (event.target === ref.current) onClose(); }} aria-label={title}><div className="dialog-header"><h2>{title}</h2><button className="icon-button" aria-label="Close dialog" onClick={onClose}><X size={20} /></button></div><div className="dialog-content">{open ? children : null}</div></dialog>;
}
export function ReportView({ value }: { value: unknown }) {
  if (value === null || value === undefined) return <span className="muted">Not recorded</span>;
  if (typeof value !== 'object') return <p className="report-text">{String(value)}</p>;
  if (Array.isArray(value)) return value.length ? <ul className="report-list">{value.map((item, index) => <li key={index}><ReportView value={item} /></li>)}</ul> : <p className="muted">None recorded.</p>;
  return <dl className="report-fields">{Object.entries(value as Record<string, unknown>).filter(([key]) => !['id', 'source_ids', 'evidence_ids', 'claim_id', 'source_id', 'chunk_id'].includes(key)).map(([key, item]) => <div key={key}><dt>{humanize(key)}</dt><dd><ReportView value={item} /></dd></div>)}</dl>;
}
export function StatusCheck({ complete, children }: { complete: boolean; children: ReactNode }) { return <div className={`status-check ${complete ? 'complete' : ''}`}><CheckCheck size={17} /><span>{children}</span></div>; }
