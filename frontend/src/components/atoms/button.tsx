import { cva, type VariantProps } from 'class-variance-authority';
import type { ButtonHTMLAttributes } from 'react';

import { cn } from '@/lib/utils/cn';

const buttonVariants = cva(
  'inline-flex items-center justify-center gap-2 whitespace-nowrap rounded-md text-sm font-medium transition-colors disabled:pointer-events-none disabled:opacity-50',
  {
    variants: {
      variant: {
        primary: 'bg-primary text-primary-foreground hover:opacity-90',
        outline: 'border border-input bg-card hover:bg-muted',
        ghost: 'hover:bg-muted',
      },
      size: {
        sm: 'h-8 px-3',
        md: 'h-10 px-4',
        icon: 'size-9',
      },
    },
    defaultVariants: { variant: 'outline', size: 'md' },
  },
);

export type ButtonProps = ButtonHTMLAttributes<HTMLButtonElement> &
  VariantProps<typeof buttonVariants>;

export function Button({ className, variant, size, type = 'button', ...props }: ButtonProps) {
  return (
    <button type={type} className={cn(buttonVariants({ variant, size }), className)} {...props} />
  );
}
