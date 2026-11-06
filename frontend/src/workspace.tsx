import { createContext, useContext } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { api, projectPath } from './api';
import type { Project, User } from './types';

export interface WorkspaceContext { user: User; project: Project; notify: (message: string, error?: boolean) => void; openEvidence: (sourceId: string) => void }
export const Workspace = createContext<WorkspaceContext | null>(null);
export function useWorkspace() { const context = useContext(Workspace); if (!context) throw new Error('Workspace context missing.'); return context; }
export function useProjectQuery<T>(path: string, poll = false) { const { project } = useWorkspace(); return useQuery({ queryKey: ['project', project.id, path], queryFn: () => api<T>(projectPath(project.id, path)), refetchInterval: poll ? 3000 : false }); }
export function useAction<T>(action: (payload: T) => Promise<unknown>, success: string) {
  const { project, notify } = useWorkspace();
  const client = useQueryClient();
  return useMutation({ mutationFn: action, onSuccess: () => { notify(success); void client.invalidateQueries({ queryKey: ['project', project.id] }); }, onError: (error: Error) => notify(error.message, true) });
}
export function canReview(role: string) { return ['admin', 'manager', 'lead'].includes(role); }
export function canManageSources(role: string) { return ['admin', 'manager', 'lead'].includes(role); }
