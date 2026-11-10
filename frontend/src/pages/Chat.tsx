import { useEffect, useRef, useState, type FormEvent } from 'react';
import { useQuery, useQueryClient } from '@tanstack/react-query';
import { Link } from 'react-router-dom';
import { ArrowRight, BrainCircuit, Check, MessageSquare, Plus, Send, Settings2, ShieldCheck, Trash2, WandSparkles } from 'lucide-react';
import { api, post, projectPath } from '../api';
import { Badge, Button, CitationList, Dialog, Empty, ErrorState, Loading, Notice, PageHeader, Panel } from '../ui';
import { useWorkspace } from '../workspace';
import type { Citation } from '../types';

type Effort = 'low' | 'high';
const models = ['gpt-6.1-sol', 'gpt-6-astra', 'gpt-5.6-sol'] as const;
type Model = typeof models[number];
interface AISettings { provider: string; base_url: string; model: string; protocol: 'responses' | 'chat_completions'; enabled: boolean; has_key: boolean }
interface ActionResult { resource_id?: string; status?: string; path?: string }
interface Action { id: string; kind: string; title: string; status: string; expires_at: string; result: ActionResult }
interface Option { id: string; kind: string; target_id: string; title: string }
interface Reply { answer: string; parts: { kind: string; text: string; references: string[] }[]; citations?: Citation[]; actions?: Action[]; unknowns: string[]; engine: string; warning?: string; model?: string; elapsed_ms?: number; usage?: Record<string, number> }
interface Turn { id: string; question: string; effort: Effort; status: string; response: Reply; created_at: string }
interface Conversation { id: string; title: string; updated_at: string; turns: Turn[] }
interface Summary { id: string; title: string; updated_at: string }

export function SuccessorPage() {
  const { project, user, openEvidence, notify } = useWorkspace();
  const client = useQueryClient();
  const base = projectPath(project.id, '');
  const queryBase = ['project', project.id, 'chat', user.id];
  const list = useQuery({ queryKey: [...queryBase, 'list'], queryFn: () => api<Summary[]>(base + '/chat/conversations') });
  const config = useQuery({ queryKey: [...queryBase, 'settings'], queryFn: () => api<AISettings>(base + '/ai-settings') });
  const options = useQuery({ queryKey: [...queryBase, 'actions'], queryFn: () => api<Option[]>(base + '/chat/actions') });
  const [selected, setSelected] = useState<string | null>(null);
  const active = selected || list.data?.[0]?.id;
  const detail = useQuery({ queryKey: [...queryBase, 'conversation', active], queryFn: () => api<Conversation>(base + '/chat/conversations/' + active), enabled: !!active, refetchInterval: query => query.state.data?.turns.some(t => t.status === 'running') ? 3000 : false });
  const [message, setMessage] = useState('');
  const [effort, setEffort] = useState<Effort>('low');
  const [model, setModel] = useState<Model | ''>('');
  const [busy, setBusy] = useState(false);
  const [creating, setCreating] = useState(false);
  const [pendingQuestion, setPendingQuestion] = useState('');
  const [error, setError] = useState<Error | null>(null);
  const [settingsOpen, setSettingsOpen] = useState(false);
  const [actionsOpen, setActionsOpen] = useState(false);
  const [deleteOpen, setDeleteOpen] = useState(false);
  const [actionBusy, setActionBusy] = useState<string | null>(null);
  const end = useRef<HTMLDivElement>(null);
  const currentModel = model || (models.includes(config.data?.model as Model) ? config.data!.model as Model : 'gpt-6.1-sol');
  const processing = busy || creating || !!actionBusy || !!detail.data?.turns.some(t => t.status === 'running');
  useEffect(() => { end.current?.scrollIntoView({ block: 'nearest', behavior: 'instant' }); }, [detail.data?.turns.length, pendingQuestion]);

  function store(value: Conversation) {
    setSelected(value.id);
    client.setQueryData([...queryBase, 'conversation', value.id], value);
    void client.invalidateQueries({ queryKey: [...queryBase, 'list'] });
  }
  async function create() {
    if (creating) return null;
    setCreating(true); setError(null);
    try { const value = await post<Conversation>(base + '/chat/conversations'); store(value); return value.id; }
    catch (e) { setError(e as Error); return null; }
    finally { setCreating(false); }
  }
  async function ask(value: string) {
    if (processing || value.trim().length < 3) return;
    setBusy(true); setError(null); setPendingQuestion(value);
    try {
      const id = active || await create();
      if (!id) return;
      const conversation = await post<Conversation>(base + '/chat/conversations/' + id + '/messages', { message: value, effort, model: currentModel, request_id: crypto.randomUUID() });
      store(conversation); setMessage('');
    } catch (e) { setError(e as Error); void detail.refetch(); }
    finally { setBusy(false); setPendingQuestion(''); }
  }
  async function preview(option: Option) {
    setError(null); setActionBusy(option.id);
    try {
      const id = active || await create();
      if (!id) return;
      store(await post<Conversation>(base + '/chat/conversations/' + id + '/actions', { kind: option.kind, target_id: option.target_id }));
      setActionsOpen(false);
    } catch (e) { setError(e as Error); }
    finally { setActionBusy(null); }
  }
  async function confirm(action: Action) {
    setActionBusy(action.id); setError(null);
    try {
      await post(base + '/chat/actions/' + action.id + '/confirm', { confirm: true });
      await client.invalidateQueries({ queryKey: ['project', project.id] });
      notify('Action submitted. Open its workspace to inspect the result.');
    } catch (e) { setError(e as Error); }
    finally { setActionBusy(null); }
  }
  async function remove() {
    if (!active) return;
    setBusy(true); setError(null);
    try { await api(base + '/chat/conversations/' + active, { method: 'DELETE' }); client.removeQueries({ queryKey: [...queryBase, 'conversation', active] }); setSelected(null); setDeleteOpen(false); await list.refetch(); }
    catch (e) { setError(e as Error); }
    finally { setBusy(false); }
  }
  function submit(event: FormEvent) { event.preventDefault(); void ask(message); }
  const starters = ['Which responsibilities have no backup owner?', 'Which incidents remain unresolved?', 'How is this service deployed?', 'Investigate this project for missing knowledge'];

  return <>
    <PageHeader eyebrow="Continuity · Digital successor" title="Ask the project’s memory" description="Discuss your project, inspect its evidence and move supported work forward." action={user.role === 'admin' && <Button variant="secondary" onClick={() => setSettingsOpen(true)}><Settings2 size={16} />AI settings</Button>} />
    <div className="chat-layout">
      <Panel className="chat-history" title="Your conversations" action={<Button variant="ghost" aria-label="New conversation" disabled={processing} onClick={() => void create()}><Plus size={17} /></Button>}>
        <p className="chat-history-note">Private to your account in {project.name}.</p>
        {list.isPending ? <Loading label="Loading conversations…" /> : list.error ? <ErrorState error={list.error} retry={() => void list.refetch()} /> : list.data.length ? <nav aria-label="Conversations" className="chat-history-list">{list.data.map(item => <button key={item.id} disabled={processing} className={active === item.id ? 'selected' : ''} onClick={() => { setSelected(item.id); setError(null); }}><MessageSquare size={15} /><span>{item.title}</span></button>)}</nav> : <p className="muted padded">Your saved conversations will appear here.</p>}
        {active && <Button variant="ghost" disabled={processing} onClick={() => setDeleteOpen(true)}><Trash2 size={14} />Delete conversation</Button>}
        <div className="chat-provider-state"><span className="mini-label">{config.data?.enabled ? 'AgentRouter enabled' : 'Verified retrieval'}</span><p>{config.data?.enabled ? 'Answers are generated from authorised context. Inspect the citations before acting.' : 'Ask about verified evidence now. An admin can connect AgentRouter for conversational answers.'}</p></div>
      </Panel>
      <Panel className="successor-conversation chat-conversation">
        <div className="chat-toolbar"><div><BrainCircuit size={18} /><strong>{detail.data?.title || 'New conversation'}</strong></div><Button variant="secondary" disabled={processing || !options.data?.length} onClick={() => setActionsOpen(true)}><WandSparkles size={15} />Project actions</Button></div>
        {detail.error && <ErrorState error={detail.error} retry={() => void detail.refetch()} />}
        {active && detail.isPending ? <Loading label="Loading your conversation…" /> : detail.data?.turns.length ? <div className="conversation-list chat-turns" role="log" aria-label="Project conversation" aria-live="polite">{detail.data.turns.map(turn => <section key={turn.id} className="conversation-turn">
          <div className="user-question"><MessageSquare size={17} /><p>{turn.question}</p></div>
          <div className="successor-answer"><span className="answer-avatar"><BrainCircuit size={20} /></span><div>
            <div className="answer-heading"><strong>Digital successor</strong><span className="mini-label">{turn.effort} effort{turn.response.model ? ' · ' + turn.response.model : ''}</span></div>
            {turn.status === 'running' ? <Loading label="Preparing a reply…" /> : <>
              {turn.response.parts?.length ? turn.response.parts.map((part, i) => <div key={i} className={'chat-answer-part part-' + part.kind}><span className="mini-label">{part.kind === 'project' ? 'Evidence-based explanation' : part.kind === 'status' ? 'Workspace status' : part.kind === 'guidance' ? 'General guidance' : 'Insufficient evidence'}</span><p className="answer-text">{part.text}</p></div>) : <p className="answer-text">{turn.response.answer}</p>}
              {turn.response.warning && <Notice tone="warning">{turn.response.warning}</Notice>}
              {!!turn.response.citations?.length && <details className="chat-citations"><summary>Inspect {turn.response.citations.length} supporting {turn.response.citations.length === 1 ? 'citation' : 'citations'}</summary><CitationList citations={turn.response.citations} openSource={openEvidence} /></details>}
              {turn.response.actions?.map(action => <div className="chat-action-preview" key={action.id}><div><span className="mini-label">Action preview</span><h3>{action.title}</h3><p>{action.status === 'completed' ? 'Submitted. Check the linked workspace for its current status.' : 'Confirmation uses your current project permissions. No approval, ownership acceptance or production change is performed.'}</p></div><Badge value={action.status} />{action.status === 'pending' && <Button onClick={() => void confirm(action)} busy={actionBusy === action.id} disabled={processing || !!actionBusy}>Confirm action <Check size={15} /></Button>}{action.status === 'completed' && action.result.path && <Link className="text-link" to={action.result.path}>Open result <ArrowRight size={14} /></Link>}</div>)}
              <small className="answer-engine">{turn.response.engine.replaceAll('_', ' ')}{turn.response.elapsed_ms !== undefined ? ' · ' + (turn.response.elapsed_ms / 1000).toFixed(1) + 's' : ''}{turn.response.usage?.total_tokens !== undefined ? ' · ' + turn.response.usage.total_tokens + ' tokens' : ''}</small>
            </>}
          </div></div>
        </section>)}</div> : <div className="successor-welcome"><span className="successor-emblem"><BrainCircuit size={35} /></span><h2>Your project, with context.</h2><p>Ask about decisions, troubleshooting, unfinished work and the next handover step.</p><div className="starter-questions">{starters.map(value => <button key={value} disabled={processing} onClick={() => void ask(value)}>{value}<ArrowRight size={15} /></button>)}</div></div>}
        {pendingQuestion && <div className="chat-pending"><div className="user-question"><MessageSquare size={17} /><p>{pendingQuestion}</p></div><Loading label={config.data?.enabled ? 'Reviewing context and waiting for AgentRouter… This can take up to two minutes.' : 'Retrieving authorised evidence…'} /></div>}
        <div ref={end} />
        {error && <ErrorState error={error} retry={() => void ask(message)} />}
        <form className="chat-composer" onSubmit={submit}><div className="chat-controls"><fieldset><legend className="sr-only">Reasoning effort</legend><button type="button" aria-pressed={effort === 'low'} className={effort === 'low' ? 'selected' : ''} onClick={() => setEffort('low')} disabled={processing}>Low effort</button><button type="button" aria-pressed={effort === 'high'} className={effort === 'high' ? 'selected' : ''} onClick={() => setEffort('high')} disabled={processing}>High effort</button></fieldset><label className="chat-model"><span className="sr-only">Chat model</span><select value={currentModel} onChange={e => setModel(e.target.value as Model)} disabled={processing || !config.data?.enabled}>{models.map(value => <option key={value}>{value}</option>)}</select></label></div><div className="successor-input"><label className="sr-only" htmlFor="successor-question">Ask a project question</label><textarea id="successor-question" rows={2} value={message} onChange={event => setMessage(event.target.value)} maxLength={4000} placeholder="Ask a question, describe a problem, or request a project action…" required disabled={processing} onKeyDown={event => { if (event.key === 'Enter' && !event.shiftKey && !event.nativeEvent.isComposing) { event.preventDefault(); void ask(message); } }} /><Button type="submit" busy={busy} disabled={processing || message.trim().length < 3} aria-label="Send question"><Send size={18} /></Button></div><div className="chat-composer-hint">{effort === 'low' ? 'Focused reply with a smaller evidence budget.' : 'More evidence, conversation context and detailed reasoning.'} Enter to send · Shift+Enter for a new line.</div></form>
        <div className="successor-footnote"><ShieldCheck size={13} />Project facts need accessible evidence. General guidance is labelled. Confirm actions after review.</div>
      </Panel>
    </div>
    {settingsOpen && <AISettingsDialog open close={() => setSettingsOpen(false)} value={config.data} base={base} refresh={() => { void config.refetch(); }} />}
    <Dialog open={actionsOpen} title="Choose a project action" onClose={() => setActionsOpen(false)}><Notice>Select an action to see its preview. The assistant cannot approve claims, accept ownership or run production operations.</Notice>{options.error && <ErrorState error={options.error} />}{options.data?.length ? <div className="chat-action-options">{options.data.map(option => <Button key={option.id} variant="secondary" onClick={() => void preview(option)} busy={actionBusy === option.id} disabled={!!actionBusy}>{option.title}<ArrowRight size={15} /></Button>)}</div> : <Empty title="No actions available" description="Your role or the current project state has no supported actions. You can still ask questions." />}</Dialog>
    <Dialog open={deleteOpen} title="Delete this conversation?" onClose={() => setDeleteOpen(false)}><p>This removes your saved messages and action previews. It does not undo project actions that were already confirmed.</p><Button variant="danger" onClick={() => void remove()} busy={busy}>Delete conversation</Button></Dialog>
  </>;
}

function AISettingsDialog({ open, close, value, base, refresh }: { open: boolean; close: () => void; value?: AISettings; base: string; refresh: () => void }) {
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<Error | null>(null);
  const [result, setResult] = useState('');
  async function save(event: FormEvent<HTMLFormElement>) {
    event.preventDefault(); const form = event.currentTarget; const fields = new FormData(form);
    setBusy(true); setError(null); setResult('');
    try {
      await api(base + '/ai-settings', { method: 'PUT', body: JSON.stringify({ base_url: fields.get('base_url'), model: fields.get('model'), protocol: fields.get('protocol'), enabled: fields.get('enabled') === 'on', api_key: String(fields.get('api_key') || '') || undefined }) });
      (form.elements.namedItem('api_key') as HTMLInputElement).value = '';
      refresh(); setResult('Settings saved. Use Test connection to check the provider.');
    } catch (e) { setError(e as Error); }
    finally { setBusy(false); }
  }
  async function test() { setBusy(true); setError(null); setResult(''); try { const r = await post<{ model: string }>(base + '/ai-settings/test'); setResult('Connection successful for ' + r.model + '.'); } catch (e) { setError(e as Error); } finally { setBusy(false); } }
  async function disconnect() { setBusy(true); setError(null); try { await api(base + '/ai-settings', { method: 'DELETE' }); refresh(); setResult('Provider disconnected and saved key removed.'); } catch (e) { setError(e as Error); } finally { setBusy(false); } }
  return <Dialog open={open} title="Organisation AI settings" onClose={() => { if (!busy) close(); }}><p>These settings apply to your organisation. Enabling AI sends authorised context and recent conversation messages to AgentRouter. Review its data policies before using confidential sources.</p><form key={value?.model + String(value?.enabled) + value?.base_url} className="form-stack" onSubmit={save}><label>API endpoint<select name="base_url" defaultValue={value?.base_url || 'https://agentrouter.org/v1'}><option value="https://agentrouter.org/v1">agentrouter.org</option><option value="https://ps.air-outer.com/v1">ps.air-outer.com</option></select></label><label>Default model<select name="model" defaultValue={models.includes(value?.model as Model) ? value!.model : 'gpt-6.1-sol'}>{models.map(m => <option key={m}>{m}</option>)}</select></label><label>API protocol<select name="protocol" defaultValue={value?.protocol || 'responses'}><option value="responses">Responses</option><option value="chat_completions">Chat Completions</option></select></label><label>Provider API key<input name="api_key" type="password" autoComplete="off" maxLength={300} minLength={12} placeholder={value?.has_key ? 'Saved securely · leave blank to keep it' : 'Enter your AgentRouter key'} /></label><label className="checkbox-label"><input name="enabled" type="checkbox" defaultChecked={value?.enabled || false} />Enable external AI processing for authorised users</label><Notice>The key is encrypted on the server and never returned to the browser. Keep keys out of messages and source files.</Notice><div className="chat-settings-actions"><Button type="submit" busy={busy}>Save settings</Button><Button type="button" variant="secondary" onClick={() => void test()} disabled={busy || !value?.has_key}>Test connection</Button>{value?.has_key && <Button type="button" variant="ghost" onClick={() => void disconnect()} disabled={busy}>Disconnect</Button>}</div></form>{busy && <Loading label="Waiting for provider or saving settings…" />}{error && <ErrorState error={error} />}{result && <Notice tone="success">{result}</Notice>}</Dialog>;
}
