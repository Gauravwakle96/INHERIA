let csrfToken = '';
export function setCsrfToken(value: string) { csrfToken = value; }

export class ApiError extends Error {
  status: number;
  requestId?: string;
  retryAt?: number;
  constructor(message: string, status: number, requestId?: string, retryAfter?: number) { super(message); this.status = status; this.requestId = requestId; this.retryAt = retryAfter ? Date.now() + retryAfter * 1000 : undefined; }
}

export async function api<T>(path: string, options: RequestInit = {}): Promise<T> {
  const method = options.method || 'GET';
  const headers = new Headers(options.headers);
  if (options.body && !(options.body instanceof FormData)) headers.set('Content-Type', 'application/json');
  if (!['GET', 'HEAD', 'OPTIONS'].includes(method) && csrfToken) headers.set('X-CSRF-Token', csrfToken);
  const controller = new AbortController();
  const timeout = window.setTimeout(() => controller.abort(), path.includes('/messages') ? 130000 : 60000);
  let response: Response;
  try {
    response = await fetch(`/api${path}`, { ...options, signal: options.signal || controller.signal, headers, credentials: 'same-origin' });
  } catch (error) {
    if (controller.signal.aborted) throw new ApiError('The request timed out. Your work may already be saved; refresh and inspect the result before retrying.', 408);
    throw error;
  } finally {
    window.clearTimeout(timeout);
  }
  const body: unknown = await response.json().catch(() => ({}));
  if (!response.ok) {
    const data = body as { detail?: unknown; request_id?: string };
    const detail = typeof data.detail === 'string' ? data.detail : response.status === 422 ? 'Check the form fields and try again.' : `Request failed (${response.status}).`;
    const retryHeader = response.headers.get('Retry-After');
    const retrySeconds = retryHeader ? Number(retryHeader) : 0;
    throw new ApiError(detail, response.status, data.request_id, response.status === 429 ? Number.isFinite(retrySeconds) && retrySeconds > 0 ? Math.min(retrySeconds, 300) : 60 : undefined);
  }
  return body as T;
}

export const post = <T>(path: string, body: unknown = {}) => api<T>(path, { method: 'POST', body: JSON.stringify(body) });
export const patch = <T>(path: string, body: unknown) => api<T>(path, { method: 'PATCH', body: JSON.stringify(body) });
export const projectPath = (projectId: string, path: string) => `/projects/${encodeURIComponent(projectId)}${path}`;
