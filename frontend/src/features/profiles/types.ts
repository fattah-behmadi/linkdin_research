/**
 * Domain model of the profiles feature.
 *
 * Deliberately camelCase and free of API concerns: the wire shapes live in
 * `api/profile.dto.ts` and are translated by `mappers/profile.mapper.ts`, so a
 * change in the backend contract stops at the mapper.
 */

export const SORT_OPTIONS = ['relevance', 'experience_desc', 'experience_asc', 'name'] as const;
export type SortOption = (typeof SORT_OPTIONS)[number];

export interface Experience {
  title: string | null;
  companyName: string | null;
  companyIndustry: string | null;
  locationName: string | null;
  startDate: string | null;
  endDate: string | null;
  isCurrent: boolean;
}

export interface Education {
  schoolName: string | null;
  degrees: string[];
  majors: string[];
  startDate: string | null;
  endDate: string | null;
}

export interface ProfileSummary {
  id: number;
  fullName: string;
  headline: string | null;
  jobTitle: string | null;
  companyName: string | null;
  industry: string | null;
  locationName: string | null;
  country: string | null;
  seniority: string | null;
  yearsExperience: number | null;
  linkedinUrl: string | null;
  skills: string[];
  score: number | null;
}

export interface ProfileDetail extends ProfileSummary {
  summary: string | null;
  companySize: string | null;
  companyIndustry: string | null;
  connections: number | null;
  inferredSalary: string | null;
  experiences: Experience[];
  educations: Education[];
}

export interface SearchResult {
  items: ProfileSummary[];
  total: number;
  page: number;
  size: number;
  pages: number;
  tookMs: number;
  backend: string;
}

export interface FacetValue {
  value: string;
  count: number;
}

export interface Facets {
  skills: FacetValue[];
  industries: FacetValue[];
  countries: FacetValue[];
  seniorities: FacetValue[];
  companySizes: FacetValue[];
}

/** Every facet the UI can filter on, keyed the way the domain names them. */
export type FacetKey = keyof Facets;

/** The search state the UI owns (and mirrors into the URL). */
export interface SearchCriteria {
  q: string;
  skills: string[];
  industries: string[];
  countries: string[];
  seniorities: string[];
  companySizes: string[];
  minYears: number | null;
  maxYears: number | null;
  page: number;
  size: number;
  sort: SortOption;
}

export const DEFAULT_CRITERIA: SearchCriteria = {
  q: '',
  skills: [],
  industries: [],
  countries: [],
  seniorities: [],
  companySizes: [],
  minYears: null,
  maxYears: null,
  page: 1,
  size: 20,
  sort: 'relevance',
};

export function countActiveFilters(criteria: SearchCriteria): number {
  return (
    criteria.skills.length +
    criteria.industries.length +
    criteria.countries.length +
    criteria.seniorities.length +
    criteria.companySizes.length +
    (criteria.minYears !== null ? 1 : 0) +
    (criteria.maxYears !== null ? 1 : 0)
  );
}
