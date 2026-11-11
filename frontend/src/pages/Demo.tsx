import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { Link } from 'react-router-dom';
import { ArrowRight, CheckCircle2, GitBranch, ShieldCheck, Users } from 'lucide-react';
import { api, post } from '../api';
import type { Claim, Session, Transition } from '../types';
import { Button, ErrorState, Notice, Panel } from '../ui';
import { ThemeToggle } from '../ThemeToggle';
import { useProjectQuery, useWorkspace } from '../workspace';

const steps = [
  ['Connect', 'Rudransh', '/sources', 'Inspect authorised runbooks, decisions and issue notes. Upload a document of your own to test a fresh input.'],
  ['Reconstruct', 'Rudransh', '/investigation', 'Run an investigation. It finds candidate responsibilities, dependencies, decisions and missing recovery knowledge.'],
  ['Verify & review', 'Rudransh', '/memory', 'Open a claim and inspect its exact source. Approve supported information, reject unsupported claims and resolve conflicting decisions.'],
  ['Handover', 'Rudransh', '/handover', 'Generate and approve a version, assign Gaurav’s responsibilities to Savinay and create practical validation tasks.'],
  ['Accept & validate', 'Savinay', '/validation', 'Switch persona in the topbar. Review assignments, accept or reject ownership, then submit a cited walkthrough and escalation path.'],
  ['Assess & recover', 'Rudransh', '/validation', 'Review practical criteria. Request revision when evidence is incomplete. Close only after acceptance, review and required prerequisites.'],
];

export function DemoPage({ onLogin }: { onLogin: (session: Session) => void }) {
  const config = useQuery({ queryKey: ['judge-demo-info'], queryFn: () => api<{ enabled: boolean; expires_hours: number }>('/auth/judge-demo') });
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<Error | null>(null);
  async function start() {
    setBusy(true); setError(null);
    try { onLogin(await post<Session>('/auth/judge-demo/start')); } catch (e) { setError(e as Error); } finally { setBusy(false); }
  }
  return <div className="demo-page"><header className="demo-top"><Link to="/" className="brand">INHERIA.</Link><div><ThemeToggle /><Link to="/">Sign in</Link></div></header><main id="main-content">
    <section className="demo-hero"><div className="eyebrow">Explore the complete handover</div><h1>Gaurav leaves.<br /><span>Savinay can continue.</span></h1><p>ShopEase is a shopping application. Its DevOps engineer owns releases, alerts and recovery knowledge. Follow the team as they turn scattered sources into a reviewed continuation plan.</p><div className="demo-cta"><Button busy={busy} disabled={!config.data?.enabled} onClick={() => void start()}>Start interactive demo <ArrowRight size={18} /></Button><span>No account or API key needed · Your own isolated workspace</span></div>{error && <ErrorState error={error} />}{config.error && <ErrorState error={config.error} retry={() => void config.refetch()} />}{config.data && !config.data.enabled && <Notice tone="warning">Interactive demo is currently unavailable. The walkthrough below remains accessible.</Notice>}</section>
    <div className="demo-people">{[['Gaurav', 'Departing DevOps engineer', 'Knows deployments, alert triage and recovery gaps.'], ['Savinay', 'Incoming DevOps engineer', 'Reviews knowledge, accepts ownership and demonstrates understanding.'], ['Rudransh', 'Administrator & coordinator', 'Controls sources, review, access and transition closure.']].map(([name, role, detail]) => <Panel key={name}><Users size={23} /><h2>{name}</h2><strong>{role}</strong><p>{detail}</p></Panel>)}</div>
    <section className="demo-section"><h2>The central workflow, including what can go wrong</h2><div className="demo-steps">{steps.map(([name, person, , detail], i) => <article key={name}><span className="demo-step-number">{String(i + 1).padStart(2, '0')}</span><div><h3>{name}</h3><small>{person}</small><p>{detail}</p></div></article>)}</div></section>
    <div className="demo-people"><Panel title="Traceable"><GitBranch /><p>Open exact excerpts, document names, locations and versions behind every important claim. Source statements begin pending human verification.</p></Panel><Panel title="Actionable"><CheckCircle2 /><p>Savinay sees ownership, unresolved issues, procedures and next tasks. Missing restore evidence remains a blocker until it is reviewed.</p></Panel><Panel title="Permission-aware"><ShieldCheck /><p>A coordinator-only source stays hidden from Savinay. Persona switching applies only to your own case-study accounts.</p></Panel></div>
    <Notice><strong>About this case study.</strong> ShopEase and its records are authored examples of a realistic DevOps handover, not Wipro/client records or completed cloud tests. Actions you perform are recorded as demo actions. The workspace expires after {config.data?.expires_hours || 4} hours. Use only information you are authorised to share; do not upload confidential production data into the demo.</Notice>
  </main><footer className="workspace-footer"><span>INHERIA · People leave. Knowledge lives on.</span><Link to="/">Open your own workspace <ArrowRight size={14} /></Link></footer></div>;
}

export function DemoGuide() {
  const { user } = useWorkspace();
  const claims = useProjectQuery<Claim[]>('/claims', true);
  const transitions = useProjectQuery<Transition[]>('/transitions');
  const [expanded, setExpanded] = useState(true);
  const transition = transitions.data?.[0];
  const count = claims.data?.length || 0;
  return <section className="demo-guide" aria-label="Demo next steps"><div className="demo-guide-heading"><div><strong>ShopEase handover · You are {user.name}</strong><p>{user.name === 'Savinay' ? 'Review your handover and submit practical evidence. Only you can accept your assigned ownership.' : user.name === 'Gaurav' ? 'Inspect your responsibilities and record targeted explanations in Investigation → Remediation tasks.' : count ? 'Inspect evidence, review supported claims and build the handover. All approvals require your action.' : 'Start in Investigation to reconstruct the preloaded project sources.'}</p></div><Button variant="ghost" onClick={() => setExpanded(!expanded)} aria-expanded={expanded}>{expanded ? 'Hide guide' : 'Show guide'}</Button></div>{expanded && <><nav aria-label="Demo workflow">{steps.map(([name, person, path]) => <Link to={path} key={name}><span>{name}</span><small>{person}</small></Link>)}</nav><p className="muted">{count} source-linked candidates · {claims.data?.filter(c => c.status === 'verified').length || 0} reviewed · {transition?.transfers.filter(t => t.status === 'accepted').length || 0} responsibilities accepted. Switch personas using the topbar. This is your isolated case study; source evidence and required checks determine progress.</p></>}</section>;
}
