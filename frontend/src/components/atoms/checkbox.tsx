import type { InputHTMLAttributes } from 'react';

import { cn } from '@/lib/utils/cn';

export type CheckboxProps = Omit<InputHTMLAttributes<HTMLInputElement>, 'type'>;

/**
 * The native control, styled. It already gives us keyboard support, the
 * indeterminate state and screen-reader semantics for free.
 */
export function Checkbox({ className, ...props }: CheckboxProps) {
  return (
    <input
      type="checkbox"
      className={cn('accent-primary size-4 shrink-0 cursor-pointer', className)}
      {...props}
    />
  );
}
