import { z } from 'zod';

/**
 * Wire contract (snake_case), validated at runtime.
 *
 * These schemas are the single source of truth for what the API returns; the
 * mapper turns them into the domain model.
 */

export const experienceDtoSchema = z.object({
  title: z.string().nullable(),
  company_name: z.string().nullable(),
  company_industry: z.string().nullable(),
  location_name: z.string().nullable(),
  start_date: z.string().nullable(),
  end_date: z.string().nullable(),
  is_current: z.boolean(),
});

export const educationDtoSchema = z.object({
  school_name: z.string().nullable(),
  degrees: z.array(z.string()),
  majors: z.array(z.string()),
  start_date: z.string().nullable(),
  end_date: z.string().nullable(),
});

export const profileSummaryDtoSchema = z.object({
  id: z.number().int(),
  full_name: z.string(),
  headline: z.string().nullable(),
  job_title: z.string().nullable(),
  company_name: z.string().nullable(),
  industry: z.string().nullable(),
  location_name: z.string().nullable(),
  country: z.string().nullable(),
  seniority: z.string().nullable(),
  years_experience: z.number().nullable(),
  linkedin_url: z.string().nullable(),
  skills: z.array(z.string()),
  score: z.number().nullable(),
});

export const profileDetailDtoSchema = profileSummaryDtoSchema.extend({
  summary: z.string().nullable(),
  company_size: z.string().nullable(),
  company_industry: z.string().nullable(),
  connections: z.number().int().nullable(),
  inferred_salary: z.string().nullable(),
  experiences: z.array(experienceDtoSchema),
  educations: z.array(educationDtoSchema),
});

export const searchResultDtoSchema = z.object({
  items: z.array(profileSummaryDtoSchema),
  total: z.number().int(),
  page: z.number().int(),
  size: z.number().int(),
  pages: z.number().int(),
  took_ms: z.number().int(),
  backend: z.string(),
});

export const facetValueDtoSchema = z.object({
  value: z.string(),
  count: z.number().int(),
});

export const facetsDtoSchema = z.object({
  skills: z.array(facetValueDtoSchema),
  industries: z.array(facetValueDtoSchema),
  countries: z.array(facetValueDtoSchema),
  seniorities: z.array(facetValueDtoSchema),
  company_sizes: z.array(facetValueDtoSchema),
});

export type ProfileSummaryDto = z.infer<typeof profileSummaryDtoSchema>;
export type ProfileDetailDto = z.infer<typeof profileDetailDtoSchema>;
export type SearchResultDto = z.infer<typeof searchResultDtoSchema>;
export type FacetsDto = z.infer<typeof facetsDtoSchema>;
export type FacetValueDto = z.infer<typeof facetValueDtoSchema>;
