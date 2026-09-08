import { AlertTriangle, SearchX } from 'lucide-react';
import type { ReactNode } from 'react';

interface StatusMessageProps {
  icon: 'empty' | 'error';
  title: string;
  description: string;
  action?: ReactNode;
}

export function StatusMessage({ icon, title, description, action }: StatusMessageProps) {
  const Icon = icon === 'empty' ? SearchX : AlertTriangle;
  return (
    <div
      role={icon === 'error' ? 'alert' : 'status'}
      className="border-border flex flex-col items-center gap-2 rounded-lg border border-dashed px-6 py-14 text-center"
    >
      <Icon
        aria-hidden
        className={icon === 'error' ? 'text-destructive size-6' : 'text-muted-foreground size-6'}
      />
      <p className="font-medium">{title}</p>
      <p className="text-muted-foreground max-w-md text-sm">{description}</p>
      {action}
    </div>
  );
}
