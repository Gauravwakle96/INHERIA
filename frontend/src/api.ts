let csrfToken = '';
export function setCsrfToken(value: string) { csrfToken = value; }

export class ApiError extends Error {
  status: number;
  requestId?: string;
  constructor(message: string, status: number, requestId?: string) { super(message); this.status = status; this.requestId = requestId; }
}

export async function api<T>(path: string, options: RequestInit = {}): Promise<T> {
  const method = options.method || 'GET';
  const headers = new Headers(options.headers);
  if (options.body && !(options.body instanceof FormData)) headers.set('Content-Type', 'application/json');
  if (!['GET', 'HEAD', 'OPTIONS'].includes(method) && csrfToken) headers.set('X-CSRF-Token', csrfToken);
  const response = await fetch(`/api${path}`, { ...options, headers, credentials: 'same-origin' });
  const body: unknown = await response.json().catch(() => ({}));
  if (!response.ok) {
    const data = body as { detail?: unknown; request_id?: string };
    const detail = typeof data.detail === 'string' ? data.detail : response.status === 422 ? 'Check the form fields and try again.' : `Request failed (${response.status}).`;
    throw new ApiError(detail, response.status, data.request_id);
  }
  return body as T;
}

export const post = <T>(path: string, body: unknown = {}) => api<T>(path, { method: 'POST', body: JSON.stringify(body) });
export const patch = <T>(path: string, body: unknown) => api<T>(path, { method: 'PATCH', body: JSON.stringify(body) });
export const projectPath = (projectId: string, path: string) => `/projects/${encodeURIComponent(projectId)}${path}`;
