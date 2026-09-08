'use client';

import { usePathname, useRouter, useSearchParams } from 'next/navigation';
import { useCallback, useMemo } from 'react';

import {
  DEFAULT_CRITERIA,
  SORT_OPTIONS,
  type FacetKey,
  type SearchCriteria,
  type SortOption,
} from '@/features/profiles/types';

/**
 * The search state lives in the URL: results stay shareable, the back button
 * works, and there is exactly one source of truth for the query.
 */

const LIST_PARAMS: Record<FacetKey, string> = {
  skills: 'skills',
  industries: 'industries',
  countries: 'countries',
  seniorities: 'seniorities',
  companySizes: 'company_sizes',
};

function readNumber(value: string | null, fallback: number, min: number, max: number): number {
  // `Number(null)` is 0, not NaN - an absent parameter has to be handled first.
  if (value === null || value.trim() === '') return fallback;
  const parsed = Number(value);
  if (!Number.isFinite(parsed)) return fallback;
  return Math.min(Math.max(Math.trunc(parsed), min), max);
}

function readOptionalNumber(value: string | null): number | null {
  if (value === null || value.trim() === '') return null;
  const parsed = Number(value);
  return Number.isFinite(parsed) ? parsed : null;
}

function readSort(value: string | null): SortOption {
  return SORT_OPTIONS.find((option) => option === value) ?? DEFAULT_CRITERIA.sort;
}

export function parseCriteria(params: URLSearchParams): SearchCriteria {
  return {
    q: params.get('q') ?? '',
    skills: params.getAll(LIST_PARAMS.skills),
    industries: params.getAll(LIST_PARAMS.industries),
    countries: params.getAll(LIST_PARAMS.countries),
    seniorities: params.getAll(LIST_PARAMS.seniorities),
    companySizes: params.getAll(LIST_PARAMS.companySizes),
    minYears: readOptionalNumber(params.get('min_years')),
    maxYears: readOptionalNumber(params.get('max_years')),
    page: readNumber(params.get('page'), DEFAULT_CRITERIA.page, 1, 1000),
    size: readNumber(params.get('size'), DEFAULT_CRITERIA.size, 1, 100),
    sort: readSort(params.get('sort')),
  };
}

export function serializeCriteria(criteria: SearchCriteria): string {
  const params = new URLSearchParams();
  if (criteria.q.trim()) params.set('q', criteria.q.trim());
  for (const [key, param] of Object.entries(LIST_PARAMS) as [FacetKey, string][]) {
    criteria[key].forEach((value) => params.append(param, value));
  }
  if (criteria.minYears !== null) params.set('min_years', String(criteria.minYears));
  if (criteria.maxYears !== null) params.set('max_years', String(criteria.maxYears));
  if (criteria.page !== DEFAULT_CRITERIA.page) params.set('page', String(criteria.page));
  if (criteria.size !== DEFAULT_CRITERIA.size) params.set('size', String(criteria.size));
  if (criteria.sort !== DEFAULT_CRITERIA.sort) params.set('sort', criteria.sort);
  return params.toString();
}

export interface SearchCriteriaController {
  criteria: SearchCriteria;
  /** Merge a partial change; any change other than paging resets to page 1. */
  patch: (changes: Partial<SearchCriteria>) => void;
  toggleFacetValue: (facet: FacetKey, value: string) => void;
  clearFilters: () => void;
}

export function useSearchCriteria(): SearchCriteriaController {
  const router = useRouter();
  const pathname = usePathname();
  const searchParams = useSearchParams();

  const criteria = useMemo(
    () => parseCriteria(new URLSearchParams(searchParams.toString())),
    [searchParams],
  );

  const commit = useCallback(
    (next: SearchCriteria) => {
      const query = serializeCriteria(next);
      router.replace(query ? `${pathname}?${query}` : pathname, { scroll: false });
    },
    [pathname, router],
  );

  const patch = useCallback(
    (changes: Partial<SearchCriteria>) => {
      const resetsPaging = !('page' in changes);
      commit({ ...criteria, ...changes, page: resetsPaging ? 1 : (changes.page ?? criteria.page) });
    },
    [commit, criteria],
  );

  const toggleFacetValue = useCallback(
    (facet: FacetKey, value: string) => {
      const current = criteria[facet];
      const next = current.includes(value)
        ? current.filter((item) => item !== value)
        : [...current, value];
      patch({ [facet]: next } as Partial<SearchCriteria>);
    },
    [criteria, patch],
  );

  const clearFilters = useCallback(() => {
    commit({ ...DEFAULT_CRITERIA, q: criteria.q, sort: criteria.sort, size: criteria.size });
  }, [commit, criteria.q, criteria.size, criteria.sort]);

  return { criteria, patch, toggleFacetValue, clearFilters };
}
