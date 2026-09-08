import { z } from 'zod';

/**
 * Public runtime configuration.
 *
 * `process.env.NEXT_PUBLIC_*` is inlined at build time, so it has to be read
 * through the full literal - destructuring or dynamic keys would not be
 * replaced by the bundler.
 */
const schema = z.object({
  apiBaseUrl: z.url(),
});

export const env = schema.parse({
  apiBaseUrl: process.env.NEXT_PUBLIC_API_BASE_URL ?? 'http://localhost:8000/api/v1',
});

export type Env = z.infer<typeof schema>;
