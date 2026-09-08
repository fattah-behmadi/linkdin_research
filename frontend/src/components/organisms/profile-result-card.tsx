'use client';

import { Briefcase, ChevronDown, ExternalLink, MapPin, Timer } from 'lucide-react';
import { useState } from 'react';

import { Badge } from '@/components/atoms/badge';
import { Button } from '@/components/atoms/button';
import { Card, CardBody } from '@/components/atoms/card';
import { Skeleton } from '@/components/atoms/skeleton';
import { ProfileDetailView } from '@/components/molecules/profile-detail-view';
import { SkillChips } from '@/components/molecules/skill-chips';
import { useProfile } from '@/features/profiles/hooks/use-profiles';
import type { ProfileSummary } from '@/features/profiles/types';

interface ProfileResultCardProps {
  profile: ProfileSummary;
  selectedSkills: string[];
  onSkillSelect: (skill: string) => void;
}

/** One search hit. The full record is fetched only when the card is expanded. */
export function ProfileResultCard({
  profile,
  selectedSkills,
  onSkillSelect,
}: ProfileResultCardProps) {
  const [expanded, setExpanded] = useState(false);
  const detail = useProfile(profile.id, expanded);
  const panelId = `profile-detail-${profile.id}`;

  return (
    <Card className="transition-shadow hover:shadow-sm">
      <CardBody className="space-y-3">
        <div className="flex flex-wrap items-start justify-between gap-2">
          <div className="min-w-0">
            <h3 className="text-base font-semibold capitalize">{profile.fullName}</h3>
            {profile.headline && (
              <p className="text-muted-foreground text-sm capitalize">{profile.headline}</p>
            )}
          </div>
          {profile.linkedinUrl && (
            <a
              href={`https://${profile.linkedinUrl.replace(/^https?:\/\//, '')}`}
              target="_blank"
              rel="noopener noreferrer"
              className="text-primary inline-flex shrink-0 items-center gap-1 text-sm hover:underline"
            >
              LinkedIn <ExternalLink className="size-3.5" />
            </a>
          )}
        </div>

        <ul className="text-muted-foreground flex flex-wrap items-center gap-x-4 gap-y-1 text-xs">
          {profile.locationName && (
            <li className="inline-flex items-center gap-1 capitalize">
              <MapPin aria-hidden className="size-3.5" />
              {profile.locationName}
            </li>
          )}
          {profile.industry && (
            <li className="inline-flex items-center gap-1 capitalize">
              <Briefcase aria-hidden className="size-3.5" />
              {profile.industry}
            </li>
          )}
          {profile.yearsExperience !== null && (
            <li className="inline-flex items-center gap-1">
              <Timer aria-hidden className="size-3.5" />
              {profile.yearsExperience} yrs experience
            </li>
          )}
          {profile.seniority && (
            <li>
              <Badge variant="outline" className="capitalize">
                {profile.seniority}
              </Badge>
            </li>
          )}
        </ul>

        <SkillChips skills={profile.skills} highlighted={selectedSkills} onSelect={onSkillSelect} />

        <div>
          <Button
            variant="ghost"
            size="sm"
            aria-expanded={expanded}
            aria-controls={panelId}
            onClick={() => setExpanded((current) => !current)}
            className="text-primary -ml-2"
          >
            {expanded ? 'Hide details' : 'View details'}
            <ChevronDown
              aria-hidden
              className={
                expanded ? 'size-4 rotate-180 transition-transform' : 'size-4 transition-transform'
              }
            />
          </Button>
        </div>

        {expanded && (
          <div id={panelId} className="border-border border-t pt-4">
            {detail.isPending && (
              <div className="space-y-2">
                <Skeleton className="h-4 w-full" />
                <Skeleton className="h-4 w-2/3" />
              </div>
            )}
            {detail.isError && (
              <p role="alert" className="text-destructive text-sm">
                Could not load this profile.
              </p>
            )}
            {detail.data && <ProfileDetailView profile={detail.data} />}
          </div>
        )}
      </CardBody>
    </Card>
  );
}
