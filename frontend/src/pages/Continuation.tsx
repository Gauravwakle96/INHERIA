import { Link } from 'react-router-dom';
import { ArrowRight } from 'lucide-react';
import { Badge, CitationList, ErrorState, Loading, Notice, PageHeader, Panel } from '../ui';
import { useProjectActivityRefresh, useProjectQuery, useWorkspace } from '../workspace';
import type { Claim } from '../types';

interface Plan { stage: string; detail: string; next_action: { label: string; path: string; actor: string }; transition_id: string | null; ready: boolean; blockers: string[]; source_count: number; candidate_count: number; critical_gaps: number; responsibilities: Claim[]; procedures: Claim[]; open_work: Claim[]; unknowns: string[]; scope: string }

export function JourneyStatus() {
  useProjectActivityRefresh();
  const query = useProjectQuery<Plan>('/continuation-plan?summary=true');
  if (query.isPending) return <Loading label="Checking your next handover step…" />;
  if (query.error) return <ErrorState error={query.error} retry={() => void query.refetch()} />;
  const plan = query.data;
  return <section className="journey-status panel" aria-label="Your next handover step"><div><Badge value={plan.ready ? 'ready' : 'pending'} /><strong>{plan.stage}</strong><p>{plan.detail}</p><small>Next actor: {plan.next_action.actor} · {plan.source_count} accessible sources · {plan.candidate_count} knowledge records</small></div><Link className="text-link" to={plan.next_action.path}>{plan.next_action.label} <ArrowRight size={16} /></Link>{plan.blockers.length > 0 && <details><summary>{plan.blockers.length} remaining readiness checks</summary><ul>{plan.blockers.map((b,i) => <li key={i}>{b}</li>)}</ul></details>}</section>;
}

export function ContinuationPage() {
  const { user, openEvidence } = useWorkspace();
  const query = useProjectQuery<Plan>('/continuation-plan');
  return <><PageHeader eyebrow="Your work · Evidence and next actions" title={`${user.name}’s continuation plan`} description="Find your responsibilities, approved procedures and work that still needs attention." />{query.isPending ? <Loading /> : query.error ? <ErrorState error={query.error} retry={() => void query.refetch()} /> : <>{([['My responsibilities', query.data.responsibilities], ['Approved procedures', query.data.procedures], ['Open work to continue', query.data.open_work]] as [string, Claim[]][]).map(([title, items]) => <Panel key={title} title={title}><div className="padded">{items.length ? items.map(c => <article className="affected-item" key={c.id}><div className="detail-meta"><h3>{c.title}</h3><Badge value={c.status} /></div><p>{c.summary}</p><CitationList citations={c.evidence} openSource={openEvidence} /></article>) : <p>No accessible records in this section. Missing evidence does not establish that no work exists.</p>}</div></Panel>)}<Panel title="Questions still requiring confirmation"><ul className="padded">{query.data.unknowns.length ? query.data.unknowns.map((q,i) => <li key={i}>{q}</li>) : <li>No recorded accessible questions. Review project coverage before treating it as complete.</li>}</ul></Panel><Notice>{query.data.scope}</Notice></>}</>;
}
