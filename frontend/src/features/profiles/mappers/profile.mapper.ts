import type {
  FacetsDto,
  FacetValueDto,
  ProfileDetailDto,
  ProfileSummaryDto,
  SearchResultDto,
} from '@/features/profiles/api/profile.dto';
import type {
  Education,
  Experience,
  Facets,
  FacetValue,
  ProfileDetail,
  ProfileSummary,
  SearchResult,
} from '@/features/profiles/types';

/** Mapper layer: the only place that knows both the wire shape and the domain shape. */

export function toFacetValue(dto: FacetValueDto): FacetValue {
  return { value: dto.value, count: dto.count };
}

export function toProfileSummary(dto: ProfileSummaryDto): ProfileSummary {
  return {
    id: dto.id,
    fullName: dto.full_name,
    headline: dto.headline,
    jobTitle: dto.job_title,
    companyName: dto.company_name,
    industry: dto.industry,
    locationName: dto.location_name,
    country: dto.country,
    seniority: dto.seniority,
    yearsExperience: dto.years_experience,
    linkedinUrl: dto.linkedin_url,
    skills: dto.skills,
    score: dto.score,
  };
}

function toExperience(dto: ProfileDetailDto['experiences'][number]): Experience {
  return {
    title: dto.title,
    companyName: dto.company_name,
    companyIndustry: dto.company_industry,
    locationName: dto.location_name,
    startDate: dto.start_date,
    endDate: dto.end_date,
    isCurrent: dto.is_current,
  };
}

function toEducation(dto: ProfileDetailDto['educations'][number]): Education {
  return {
    schoolName: dto.school_name,
    degrees: dto.degrees,
    majors: dto.majors,
    startDate: dto.start_date,
    endDate: dto.end_date,
  };
}

export function toProfileDetail(dto: ProfileDetailDto): ProfileDetail {
  return {
    ...toProfileSummary(dto),
    summary: dto.summary,
    companySize: dto.company_size,
    companyIndustry: dto.company_industry,
    connections: dto.connections,
    inferredSalary: dto.inferred_salary,
    experiences: dto.experiences.map(toExperience),
    educations: dto.educations.map(toEducation),
  };
}

export function toSearchResult(dto: SearchResultDto): SearchResult {
  return {
    items: dto.items.map(toProfileSummary),
    total: dto.total,
    page: dto.page,
    size: dto.size,
    pages: dto.pages,
    tookMs: dto.took_ms,
    backend: dto.backend,
  };
}

export function toFacets(dto: FacetsDto): Facets {
  return {
    skills: dto.skills.map(toFacetValue),
    industries: dto.industries.map(toFacetValue),
    countries: dto.countries.map(toFacetValue),
    seniorities: dto.seniorities.map(toFacetValue),
    companySizes: dto.company_sizes.map(toFacetValue),
  };
}
