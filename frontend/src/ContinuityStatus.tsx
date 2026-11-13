import { Link } from 'react-router-dom';
import { ArrowRight, CheckCircle2 } from 'lucide-react';
import { useProjectQuery } from './workspace';
import type { Contribution, ContinuitySummary } from './types';
import { date } from './formatting';
import { ErrorState } from './ui';

export function ContributionDetails({ person }: { person: Contribution }) {
  const details = [
    person.interviews ? `${person.interviews} knowledge responses` : '',
    person.responsibilities_transferred ? `${person.responsibilities_transferred} responsibilities handed over` : '',
    person.responsibilities_accepted ? `${person.responsibilities_accepted} responsibilities accepted` : '',
    person.knowledge_reviewed ? `${person.knowledge_reviewed} knowledge items reviewed` : '',
    person.walkthroughs_submitted ? `${person.walkthroughs_submitted} walkthroughs submitted` : '',
    person.walkthroughs_reviewed ? `${person.walkthroughs_reviewed} walkthroughs assessed` : '',
    person.backup_responsibilities ? `${person.backup_responsibilities} backup assignments` : '',
  ].filter(Boolean);
  return <ul className="contribution-details">{details.length ? details.map(detail => <li key={detail}>{detail}</li>) : <li>No contribution recorded in accessible evidence yet.</li>}</ul>;
}

export function ContinuityStatus() {
  const summary = useProjectQuery<ContinuitySummary>('/continuity-summary');
  if (summary.error) return <ErrorState error={summary.error} retry={() => void summary.refetch()} />;
  const completed = summary.data?.completion;
  if (!completed) return null;
  return <section className="continuity-completion" aria-label="Completed knowledge handover">
    <div className="completion-heading"><CheckCircle2 size={21} /><div><strong>{completed.current ? 'Knowledge handover completed' : 'Completed handover · evidence needs revalidation'}</strong><p>{completed.departing_name} → {completed.successor_name} · Version {completed.version} · {date(completed.closed_at)}</p></div></div>
    <div className="completion-counts"><span><strong>{completed.accepted}/{completed.total}</strong> responsibilities accepted</span><span><strong>{completed.validated}/{completed.exercise_total}</strong> knowledge walkthroughs reviewed</span></div>
    <details className="completion-contributors"><summary>See team contributions and scope</summary><ul className="completion-team">{summary.data!.contributors.map(person => <li key={person.id}><strong>{person.name}</strong><ContributionDetails person={person} /></li>)}</ul><p>{summary.data!.scope}</p></details>
    <Link className="text-link" to={'/handover?transition=' + completed.id}>Inspect completed handover <ArrowRight size={14} /></Link>
  </section>;
}
