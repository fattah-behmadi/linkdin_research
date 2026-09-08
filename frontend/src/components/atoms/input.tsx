import type { InputHTMLAttributes } from 'react';

import { cn } from '@/lib/utils/cn';

export type InputProps = InputHTMLAttributes<HTMLInputElement>;

export function Input({ className, ...props }: InputProps) {
  return (
    <input
      className={cn(
        'border-input bg-card h-10 w-full rounded-md border px-3 text-sm',
        'placeholder:text-muted-foreground disabled:opacity-50',
        className,
      )}
      {...props}
    />
  );
}
