'use client';

import { ChevronLeft, ChevronRight } from 'lucide-react';

import { Button } from '@/components/atoms/button';

interface PaginationProps {
  page: number;
  pages: number;
  onChange: (page: number) => void;
}

export function Pagination({ page, pages, onChange }: PaginationProps) {
  if (pages <= 1) return null;

  return (
    <nav aria-label="Pagination" className="flex items-center justify-center gap-3 pt-2">
      <Button size="sm" disabled={page <= 1} onClick={() => onChange(page - 1)}>
        <ChevronLeft className="size-4" /> Previous
      </Button>
      <span aria-live="polite" className="text-muted-foreground text-sm">
        Page {page} of {pages}
      </span>
      <Button size="sm" disabled={page >= pages} onClick={() => onChange(page + 1)}>
        Next <ChevronRight className="size-4" />
      </Button>
    </nav>
  );
}
