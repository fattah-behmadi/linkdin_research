'use client';

import { useState } from 'react';

import { Checkbox } from '@/components/atoms/checkbox';
import type { FacetValue } from '@/features/profiles/types';

const COLLAPSED_COUNT = 6;

interface FacetFilterGroupProps {
  title: string;
  options: FacetValue[];
  selected: string[];
  onToggle: (value: string) => void;
  isLoading?: boolean;
}

/** One filter: a checkbox per facet value, with its hit count. */
export function FacetFilterGroup({
  title,
  options,
  selected,
  onToggle,
  isLoading = false,
}: FacetFilterGroupProps) {
  const [expanded, setExpanded] = useState(false);

  // Selected values stay visible even when they fall outside the top N.
  const pinned = options.filter((option) => selected.includes(option.value));
  const rest = options.filter((option) => !selected.includes(option.value));
  const visible = expanded ? [...pinned, ...rest] : [...pinned, ...rest].slice(0, COLLAPSED_COUNT);

  return (
    <fieldset className="border-border border-t py-4 first:border-t-0 first:pt-0">
      <legend className="mb-2 text-sm font-semibold">{title}</legend>

      {isLoading && <p className="text-muted-foreground text-xs">Loading…</p>}
      {!isLoading && options.length === 0 && (
        <p className="text-muted-foreground text-xs">No values</p>
      )}

      <ul className="space-y-1.5">
        {visible.map((option) => (
          <li key={option.value}>
            <label className="flex cursor-pointer items-center gap-2 text-sm">
              <Checkbox
                checked={selected.includes(option.value)}
                onChange={() => onToggle(option.value)}
              />
              <span className="flex-1 truncate capitalize" title={option.value}>
                {option.value}
              </span>
              <span className="text-muted-foreground text-xs tabular-nums">{option.count}</span>
            </label>
          </li>
        ))}
      </ul>

      {options.length > COLLAPSED_COUNT && (
        <button
          type="button"
          onClick={() => setExpanded((current) => !current)}
          className="text-primary mt-2 text-xs font-medium hover:underline"
        >
          {expanded ? 'Show less' : `Show all ${options.length}`}
        </button>
      )}
    </fieldset>
  );
}
