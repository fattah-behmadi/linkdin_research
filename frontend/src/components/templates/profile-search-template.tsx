'use client';

import { ChevronDown, SlidersHorizontal } from 'lucide-react';
import { useCallback, useState } from 'react';

import { useFacets, useProfileSearch } from '@/features/profiles/hooks/use-profiles';
import { useSearchCriteria } from '@/features/profiles/hooks/use-search-criteria';
import { countActiveFilters } from '@/features/profiles/types';
import { cn } from '@/lib/utils/cn';
import { Button } from '@/components/atoms/button';
import { ActiveFilters } from '@/components/molecules/active-filters';
import { SearchField } from '@/components/molecules/search-field';
import { FilterPanel } from '@/components/organisms/filter-panel';
import { ProfileResults } from '@/components/organisms/profile-results';

/**
 * Template: owns the search state (URL-backed) and lays the page out.
 * Everything below it is presentational or a single-purpose organism.
 */
export function ProfileSearchTemplate() {
  const { criteria, patch, toggleFacetValue, clearFilters } = useSearchCriteria();
  const facets = useFacets();
  const search = useProfileSearch(criteria);
  const activeFilters = countActiveFilters(criteria);
  const [filtersOpen, setFiltersOpen] = useState(false);

  // Stable so the debounced search field does not re-subscribe on every render.
  const handleQueryChange = useCallback((q: string) => patch({ q }), [patch]);

  return (
    <div className="mx-auto w-full max-w-6xl px-4 py-6 sm:px-6 lg:py-10">
      <header className="mb-6 space-y-4">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight">LinkedIn profile search</h1>
          <p className="text-muted-foreground text-sm">
            Keyword search and filtering across the profile dataset.
          </p>
        </div>

        <SearchField value={criteria.q} onChange={handleQueryChange} />

        <ActiveFilters
          criteria={criteria}
          onRemove={toggleFacetValue}
          onClearYears={() => patch({ minYears: null, maxYears: null })}
          onClearAll={clearFilters}
        />
      </header>

      <div className="grid gap-6 lg:grid-cols-[16rem_1fr]">
        {/* Collapsed by default on small screens, always visible from `lg` up. */}
        <div>
          <Button
            className="w-full justify-between lg:hidden"
            aria-expanded={filtersOpen}
            aria-controls="filter-panel"
            onClick={() => setFiltersOpen((open) => !open)}
          >
            <span className="inline-flex items-center gap-2">
              <SlidersHorizontal aria-hidden className="size-4" />
              Filters{activeFilters > 0 && ` (${activeFilters})`}
            </span>
            <ChevronDown
              aria-hidden
              className={cn('size-4 transition-transform', filtersOpen && 'rotate-180')}
            />
          </Button>
          <aside
            id="filter-panel"
            className={cn(
              'mt-3 lg:sticky lg:top-6 lg:mt-0 lg:block lg:self-start',
              filtersOpen ? 'block' : 'hidden',
            )}
          >
            <FilterPanel
              criteria={criteria}
              facets={facets.data}
              isLoading={facets.isPending}
              activeCount={activeFilters}
              onToggle={toggleFacetValue}
              onYearsChange={(range) => patch(range)}
              onClear={clearFilters}
            />
          </aside>
        </div>

        <main>
          <ProfileResults
            result={search.data}
            isPending={search.isPending}
            isFetching={search.isFetching}
            error={search.error}
            sort={criteria.sort}
            selectedSkills={criteria.skills}
            onSortChange={(sort) => patch({ sort })}
            onPageChange={(page) => patch({ page })}
            onSkillSelect={(skill) => toggleFacetValue('skills', skill)}
            onClearFilters={clearFilters}
          />
        </main>
      </div>
    </div>
  );
}
