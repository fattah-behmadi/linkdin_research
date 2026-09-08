'use client';

import { Search, X } from 'lucide-react';
import { useEffect, useState } from 'react';

import { Input } from '@/components/atoms/input';
import { useDebouncedValue } from '@/hooks/use-debounced-value';

interface SearchFieldProps {
  value: string;
  onChange: (value: string) => void;
  placeholder?: string;
}

/**
 * Debounced search box. Typing updates local state immediately (so the input
 * never lags behind the keyboard) and notifies the parent 300ms later.
 *
 * `onChange` must be referentially stable (the caller wraps it in `useCallback`),
 * otherwise the notifying effect would re-run on every render.
 */
export function SearchField({ value, onChange, placeholder }: SearchFieldProps) {
  const [draft, setDraft] = useState(value);
  const [syncedValue, setSyncedValue] = useState(value);
  const debounced = useDebouncedValue(draft, 300);

  // Adjust during render (React's documented alternative to a sync effect) when
  // the value changes elsewhere: browser back, or "clear all filters".
  if (value !== syncedValue) {
    setSyncedValue(value);
    setDraft(value);
  }

  useEffect(() => {
    if (debounced !== syncedValue) onChange(debounced);
  }, [debounced, syncedValue, onChange]);

  return (
    <div className="relative">
      <Search
        aria-hidden
        className="text-muted-foreground pointer-events-none absolute top-1/2 left-3 size-4 -translate-y-1/2"
      />
      <Input
        type="search"
        aria-label="Search profiles"
        placeholder={placeholder ?? 'Search by name, title, company, skill or school'}
        value={draft}
        onChange={(event) => setDraft(event.target.value)}
        className="h-11 pr-10 pl-9"
      />
      {draft.length > 0 && (
        <button
          type="button"
          aria-label="Clear search"
          onClick={() => setDraft('')}
          className="text-muted-foreground hover:bg-muted absolute top-1/2 right-2 -translate-y-1/2 rounded-md p-1.5"
        >
          <X className="size-4" />
        </button>
      )}
    </div>
  );
}
