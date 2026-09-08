'use client';

import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { useState, type ReactNode } from 'react';

import { HttpError } from '@/lib/http/http-client';

/** One client per browser session; created in state so it survives re-renders. */
export function Providers({ children }: { children: ReactNode }) {
  const [queryClient] = useState(
    () =>
      new QueryClient({
        defaultOptions: {
          queries: {
            refetchOnWindowFocus: false,
            // 4xx responses are contract errors - retrying them just wastes time.
            retry: (failureCount, error) =>
              !(error instanceof HttpError && error.status >= 400 && error.status < 500) &&
              failureCount < 2,
          },
        },
      }),
  );

  return <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>;
}
