'use client';

import { X } from 'lucide-react';

import { Button } from '@/components/atoms/button';
import type { FacetKey, SearchCriteria } from '@/features/profiles/types';

const FACET_LABELS: Record<FacetKey, string> = {
  skills: 'Skill',
  industries: 'Industry',
  countries: 'Country',
  seniorities: 'Seniority',
  companySizes: 'Company size',
};

interface ActiveFiltersProps {
  criteria: SearchCriteria;
  onRemove: (facet: FacetKey, value: string) => void;
  onClearYears: () => void;
  onClearAll: () => void;
}

/** Chips for everything currently narrowing the result set, each removable. */
export function ActiveFilters({
  criteria,
  onRemove,
  onClearYears,
  onClearAll,
}: ActiveFiltersProps) {
  const chips = (Object.keys(FACET_LABELS) as FacetKey[]).flatMap((facet) =>
    criteria[facet].map((value) => ({ facet, value })),
  );
  const hasYears = criteria.minYears !== null || criteria.maxYears !== null;

  if (chips.length === 0 && !hasYears) return null;

  return (
    <div className="flex flex-wrap items-center gap-2">
      {chips.map(({ facet, value }) => (
        <button
          key={`${facet}:${value}`}
          type="button"
          onClick={() => onRemove(facet, value)}
          className="bg-accent text-accent-foreground inline-flex items-center gap-1 rounded-full px-2.5 py-1 text-xs hover:opacity-80"
        >
          <span className="font-medium">{FACET_LABELS[facet]}:</span>
          <span className="capitalize">{value}</span>
          <X aria-label={`Remove ${value} filter`} className="size-3" />
        </button>
      ))}

      {hasYears && (
        <button
          type="button"
          onClick={onClearYears}
          className="bg-accent text-accent-foreground inline-flex items-center gap-1 rounded-full px-2.5 py-1 text-xs hover:opacity-80"
        >
          <span className="font-medium">Experience:</span>
          {criteria.minYears ?? 0}–{criteria.maxYears ?? 60} yrs
          <X aria-label="Remove experience filter" className="size-3" />
        </button>
      )}

      <Button variant="ghost" size="sm" onClick={onClearAll} className="text-xs">
        Clear all
      </Button>
    </div>
  );
}
