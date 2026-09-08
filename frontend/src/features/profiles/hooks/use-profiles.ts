'use client';

import { keepPreviousData, useQuery, type UseQueryResult } from '@tanstack/react-query';

import { profileService } from '@/features/profiles/services/profile.service';
import type {
  Facets,
  ProfileDetail,
  SearchCriteria,
  SearchResult,
} from '@/features/profiles/types';

/** Query keys are centralised so cache invalidation never depends on string literals. */
export const profileKeys = {
  all: ['profiles'] as const,
  search: (criteria: SearchCriteria) => [...profileKeys.all, 'search', criteria] as const,
  facets: () => [...profileKeys.all, 'facets'] as const,
  detail: (id: number) => [...profileKeys.all, 'detail', id] as const,
};

export function useProfileSearch(criteria: SearchCriteria): UseQueryResult<SearchResult> {
  return useQuery({
    queryKey: profileKeys.search(criteria),
    queryFn: ({ signal }) => profileService.search(criteria, signal),
    // Keeps the current results on screen while the next page/filter loads,
    // so the list never collapses into a spinner mid-typing.
    placeholderData: keepPreviousData,
    staleTime: 30_000,
  });
}

export function useFacets(): UseQueryResult<Facets> {
  return useQuery({
    queryKey: profileKeys.facets(),
    queryFn: ({ signal }) => profileService.facets(signal),
    staleTime: 5 * 60_000, // the dataset is a static snapshot
  });
}

export function useProfile(id: number, enabled = true): UseQueryResult<ProfileDetail> {
  return useQuery({
    queryKey: profileKeys.detail(id),
    queryFn: ({ signal }) => profileService.profile(id, signal),
    enabled,
    staleTime: 5 * 60_000,
  });
}
