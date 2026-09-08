import {
  facetsDtoSchema,
  profileDetailDtoSchema,
  searchResultDtoSchema,
  type FacetsDto,
  type ProfileDetailDto,
  type SearchResultDto,
} from '@/features/profiles/api/profile.dto';
import { httpGet, type QueryParams } from '@/lib/http/http-client';
import type { SearchCriteria } from '@/features/profiles/types';

/**
 * Proxy layer: endpoint paths and query-parameter names, nothing else.
 *
 * It returns wire DTOs on purpose - translating them is the mapper's job.
 */

function toQueryParams(criteria: SearchCriteria): QueryParams {
  return {
    q: criteria.q.trim() || undefined,
    skills: criteria.skills,
    industries: criteria.industries,
    countries: criteria.countries,
    seniorities: criteria.seniorities,
    company_sizes: criteria.companySizes,
    min_years: criteria.minYears ?? undefined,
    max_years: criteria.maxYears ?? undefined,
    page: criteria.page,
    size: criteria.size,
    sort: criteria.sort,
  };
}

export function searchProfiles(
  criteria: SearchCriteria,
  signal?: AbortSignal,
): Promise<SearchResultDto> {
  return httpGet('/profiles/search', {
    params: toQueryParams(criteria),
    schema: searchResultDtoSchema,
    signal,
  });
}

export function fetchFacets(signal?: AbortSignal): Promise<FacetsDto> {
  return httpGet('/profiles/facets', { schema: facetsDtoSchema, signal });
}

export function fetchProfile(id: number, signal?: AbortSignal): Promise<ProfileDetailDto> {
  return httpGet(`/profiles/${id}`, { schema: profileDetailDtoSchema, signal });
}
