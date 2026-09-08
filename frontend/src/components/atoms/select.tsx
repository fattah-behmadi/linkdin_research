import type { SelectHTMLAttributes } from 'react';

import { cn } from '@/lib/utils/cn';

export type SelectProps = SelectHTMLAttributes<HTMLSelectElement>;

/** Native select: accessible, and on mobile it opens the platform picker. */
export function Select({ className, ...props }: SelectProps) {
  return (
    <select
      className={cn(
        'border-input bg-card h-9 cursor-pointer rounded-md border px-2 text-sm',
        className,
      )}
      {...props}
    />
  );
}
