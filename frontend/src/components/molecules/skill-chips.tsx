'use client';

import { Badge } from '@/components/atoms/badge';
import { cn } from '@/lib/utils/cn';

interface SkillChipsProps {
  skills: string[];
  highlighted?: string[];
  limit?: number;
  onSelect?: (skill: string) => void;
}

/** Skills, with the ones the user filtered on pulled to the front and marked. */
export function SkillChips({ skills, highlighted = [], limit = 8, onSelect }: SkillChipsProps) {
  if (skills.length === 0) return null;

  const ordered = [
    ...skills.filter((skill) => highlighted.includes(skill)),
    ...skills.filter((skill) => !highlighted.includes(skill)),
  ];
  const visible = ordered.slice(0, limit);
  const remaining = ordered.length - visible.length;

  return (
    <ul className="flex flex-wrap gap-1.5">
      {visible.map((skill) => {
        const isActive = highlighted.includes(skill);
        return (
          <li key={skill}>
            <Badge
              variant={isActive ? 'accent' : 'muted'}
              className={cn('capitalize', onSelect && 'cursor-pointer hover:opacity-80')}
              onClick={onSelect ? () => onSelect(skill) : undefined}
              title={onSelect ? `Filter by ${skill}` : undefined}
            >
              {skill}
            </Badge>
          </li>
        );
      })}
      {remaining > 0 && (
        <li>
          <Badge variant="outline">+{remaining} more</Badge>
        </li>
      )}
    </ul>
  );
}
