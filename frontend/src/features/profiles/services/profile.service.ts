import { fetchFacets, fetchProfile, searchProfiles } from '@/features/profiles/api/profile.proxy';
import {
  toFacets,
  toProfileDetail,
  toSearchResult,
} from '@/features/profiles/mappers/profile.mapper';
import type {
  Facets,
  ProfileDetail,
  SearchCriteria,
  SearchResult,
} from '@/features/profiles/types';

/**
 * Service layer: proxy + mapper composed into the operations the UI actually
 * needs. React Query hooks call these and never touch HTTP or DTOs.
 */
export const profileService = {
  async search(criteria: SearchCriteria, signal?: AbortSignal): Promise<SearchResult> {
    return toSearchResult(await searchProfiles(criteria, signal));
  },

  async facets(signal?: AbortSignal): Promise<Facets> {
    return toFacets(await fetchFacets(signal));
  },

  async profile(id: number, signal?: AbortSignal): Promise<ProfileDetail> {
    return toProfileDetail(await fetchProfile(id, signal));
  },
} as const;

export type ProfileService = typeof profileService;
