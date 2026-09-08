'use client';

import { Button } from '@/components/atoms/button';
import { Pagination } from '@/components/molecules/pagination';
import { ProfileCardSkeleton } from '@/components/molecules/profile-card-skeleton';
import { SortSelect } from '@/components/molecules/sort-select';
import { StatusMessage } from '@/components/molecules/status-message';
import { ProfileResultCard } from '@/components/organisms/profile-result-card';
import type { SearchResult, SortOption } from '@/features/profiles/types';
import { HttpError } from '@/lib/http/http-client';

interface ProfileResultsProps {
  result: SearchResult | undefined;
  isPending: boolean;
  isFetching: boolean;
  error: unknown;
  sort: SortOption;
  selectedSkills: string[];
  onSortChange: (sort: SortOption) => void;
  onPageChange: (page: number) => void;
  onSkillSelect: (skill: string) => void;
  onClearFilters: () => void;
}

function describeError(error: unknown): string {
  if (error instanceof HttpError) return error.message;
  return 'Something went wrong while searching.';
}

export function ProfileResults({
  result,
  isPending,
  isFetching,
  error,
  sort,
  selectedSkills,
  onSortChange,
  onPageChange,
  onSkillSelect,
  onClearFilters,
}: ProfileResultsProps) {
  if (error) {
    return (
      <StatusMessage
        icon="error"
        title="Search failed"
        description={describeError(error)}
        action={
          <Button size="sm" onClick={() => window.location.reload()}>
            Retry
          </Button>
        }
      />
    );
  }

  if (isPending) {
    return (
      <div className="space-y-3">
        {Array.from({ length: 4 }, (_, index) => (
          <ProfileCardSkeleton key={index} />
        ))}
      </div>
    );
  }

  if (!result) return null;

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <p aria-live="polite" className="text-muted-foreground text-sm">
          <span className="text-foreground font-medium">{result.total}</span>{' '}
          {result.total === 1 ? 'profile' : 'profiles'}
          <span className="hidden sm:inline">
            {' '}
            · {result.tookMs} ms · {result.backend}
          </span>
          {isFetching && <span className="ml-2 animate-pulse">updating…</span>}
        </p>
        <SortSelect value={sort} onChange={onSortChange} />
      </div>

      {result.items.length === 0 ? (
        <StatusMessage
          icon="empty"
          title="No profiles match"
          description="Try fewer filters, or search for a broader keyword such as a skill or a job title."
          action={
            <Button size="sm" onClick={onClearFilters}>
              Clear filters
            </Button>
          }
        />
      ) : (
        <ul className="space-y-3">
          {result.items.map((profile) => (
            <li key={profile.id}>
              <ProfileResultCard
                profile={profile}
                selectedSkills={selectedSkills}
                onSkillSelect={onSkillSelect}
              />
            </li>
          ))}
        </ul>
      )}

      <Pagination page={result.page} pages={result.pages} onChange={onPageChange} />
    </div>
  );
}
