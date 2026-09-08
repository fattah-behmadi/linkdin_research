import type { ZodType } from 'zod';

import { env } from '@/lib/config/env';

/** Query values the API understands: repeated params for lists, dropped when empty. */
export type QueryParams = Record<string, string | number | boolean | string[] | undefined | null>;

export class HttpError extends Error {
  constructor(
    readonly status: number,
    readonly code: string,
    message: string,
  ) {
    super(message);
    this.name = 'HttpError';
  }
}

/** Shape of the API's error envelope: `{ "error": { "code", "message" } }`. */
function readErrorEnvelope(body: unknown, status: number): HttpError {
  if (typeof body === 'object' && body !== null && 'error' in body) {
    const error = (body as { error: { code?: string; message?: string } }).error;
    return new HttpError(status, error.code ?? 'http_error', error.message ?? 'Request failed');
  }
  return new HttpError(status, 'http_error', `Request failed with status ${status}`);
}

export function buildQueryString(params: QueryParams): string {
  const search = new URLSearchParams();
  for (const [key, value] of Object.entries(params)) {
    if (value === undefined || value === null || value === '') continue;
    if (Array.isArray(value)) {
      value.filter(Boolean).forEach((item) => search.append(key, item));
    } else {
      search.append(key, String(value));
    }
  }
  const query = search.toString();
  return query ? `?${query}` : '';
}

interface GetOptions<T> {
  params?: QueryParams;
  /** Response contract. Validating here keeps `any` out of the rest of the app. */
  schema: ZodType<T>;
  signal?: AbortSignal;
}

/**
 * The only place in the app that talks to `fetch`.
 *
 * Everything above it (proxies, services, hooks) works with typed, validated
 * data and a single `HttpError` failure mode.
 */
export async function httpGet<T>(path: string, options: GetOptions<T>): Promise<T> {
  const url = `${env.apiBaseUrl}${path}${buildQueryString(options.params ?? {})}`;

  let response: Response;
  try {
    response = await fetch(url, {
      method: 'GET',
      headers: { Accept: 'application/json' },
      signal: options.signal,
    });
  } catch (cause) {
    if (cause instanceof DOMException && cause.name === 'AbortError') throw cause;
    throw new HttpError(0, 'network_error', 'The API is unreachable. Is the backend running?');
  }

  const body: unknown = await response.json().catch(() => null);
  if (!response.ok) throw readErrorEnvelope(body, response.status);

  const parsed = options.schema.safeParse(body);
  if (!parsed.success) {
    throw new HttpError(
      response.status,
      'invalid_response',
      'The API returned an unexpected shape',
    );
  }
  return parsed.data;
}
