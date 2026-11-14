import { createContext, useContext, useEffect, useRef } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { api, projectPath } from './api';
import type { Project, User } from './types';

export interface WorkspaceContext { user: User; project: Project; notify: (message: string, error?: boolean) => void; openEvidence: (sourceId: string) => void }
export const Workspace = createContext<WorkspaceContext | null>(null);
export function useWorkspace() { const context = useContext(Workspace); if (!context) throw new Error('Workspace context missing.'); return context; }
export function useProjectQuery<T>(path: string) { const { project } = useWorkspace(); return useQuery({ queryKey: ['project', project.id, path], queryFn: () => api<T>(projectPath(project.id, path)), refetchInterval: false }); }

interface ActiveJob { id: string; kind: string; status: string }
export function useProjectActivityRefresh() {
  const { project } = useWorkspace();
  const client = useQueryClient();
  const previous = useRef<string[]>([]);
  const query = useQuery({
    queryKey: ['project', project.id, '/activity-status'],
    queryFn: () => api<ActiveJob[]>(projectPath(project.id, '/activity-status')),
    refetchInterval: query => query.state.data?.length ? 5000 : false,
    refetchIntervalInBackground: false,
  });
  useEffect(() => {
    if (!query.data) return;
    const active = query.data.map(job => job.id);
    if (previous.current.some(id => !active.includes(id))) {
      // A completed or failed job changes evidence and readiness, even when the
      // user has left its page. Refresh once, then stop polling an idle project.
      void client.invalidateQueries({ queryKey: ['project', project.id], predicate: q => q.queryKey[2] !== '/activity-status' });
    }
    previous.current = active;
  }, [query.data, project.id, client]);
}
export function useAction<T>(action: (payload: T) => Promise<unknown>, success: string) {
  const { project, notify } = useWorkspace();
  const client = useQueryClient();
  return useMutation({ mutationFn: action, onSuccess: result => {
    notify(success);
    const job = result as Partial<ActiveJob> | null;
    if (job?.id && job.status && ['queued', 'running', 'syncing'].includes(job.status)) {
      // Remember even very short jobs so completion refreshes dependent queries
      // when the first server status check already reports no active work.
      client.setQueryData<ActiveJob[]>(['project', project.id, '/activity-status'], current => [...(current || []).filter(item => item.id !== job.id), { id: job.id!, kind: job.kind || 'investigation', status: job.status! }]);
    }
    void client.invalidateQueries({ queryKey: ['project', project.id] });
  }, onError: (error: Error) => notify(error.message, true) });
}
export function canReview(role: string) { return ['admin', 'manager', 'lead'].includes(role); }
export function canManageSources(role: string) { return ['admin', 'manager', 'lead'].includes(role); }
