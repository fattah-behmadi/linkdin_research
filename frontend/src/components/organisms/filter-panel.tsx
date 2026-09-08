'use client';

import { SlidersHorizontal } from 'lucide-react';

import { Button } from '@/components/atoms/button';
import { FacetFilterGroup } from '@/components/molecules/facet-filter-group';
import { YearsRangeFilter } from '@/components/molecules/years-range-filter';
import type { FacetKey, Facets, SearchCriteria } from '@/features/profiles/types';

const GROUPS: { key: FacetKey; title: string }[] = [
  { key: 'skills', title: 'Skills' },
  { key: 'industries', title: 'Industry' },
  { key: 'countries', title: 'Country' },
  { key: 'seniorities', title: 'Seniority' },
  { key: 'companySizes', title: 'Company size' },
];

interface FilterPanelProps {
  criteria: SearchCriteria;
  facets: Facets | undefined;
  isLoading: boolean;
  activeCount: number;
  onToggle: (facet: FacetKey, value: string) => void;
  onYearsChange: (range: { minYears: number | null; maxYears: number | null }) => void;
  onClear: () => void;
}

/** All five facet filters plus the experience range. */
export function FilterPanel({
  criteria,
  facets,
  isLoading,
  activeCount,
  onToggle,
  onYearsChange,
  onClear,
}: FilterPanelProps) {
  return (
    <div className="space-y-1">
      <div className="hidden items-center justify-between pb-2 lg:flex">
        <h2 className="inline-flex items-center gap-2 text-sm font-semibold">
          <SlidersHorizontal aria-hidden className="size-4" />
          Filters
          {activeCount > 0 && (
            <span className="bg-primary text-primary-foreground rounded-full px-1.5 py-0.5 text-xs">
              {activeCount}
            </span>
          )}
        </h2>
        {activeCount > 0 && (
          <Button variant="ghost" size="sm" onClick={onClear} className="text-xs">
            Reset
          </Button>
        )}
      </div>

      {GROUPS.map(({ key, title }) => (
        <FacetFilterGroup
          key={key}
          title={title}
          options={facets?.[key] ?? []}
          selected={criteria[key]}
          isLoading={isLoading}
          onToggle={(value) => onToggle(key, value)}
        />
      ))}

      <YearsRangeFilter min={criteria.minYears} max={criteria.maxYears} onChange={onYearsChange} />
    </div>
  );
}
