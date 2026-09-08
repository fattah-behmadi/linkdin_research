'use client';

import { Select } from '@/components/atoms/select';
import type { SortOption } from '@/features/profiles/types';

const LABELS: Record<SortOption, string> = {
  relevance: 'Best match',
  experience_desc: 'Most experience',
  experience_asc: 'Least experience',
  name: 'Name (A–Z)',
};

interface SortSelectProps {
  value: SortOption;
  onChange: (value: SortOption) => void;
}

export function SortSelect({ value, onChange }: SortSelectProps) {
  return (
    <label className="text-muted-foreground flex items-center gap-2 text-sm">
      Sort
      <Select value={value} onChange={(event) => onChange(event.target.value as SortOption)}>
        {Object.entries(LABELS).map(([option, label]) => (
          <option key={option} value={option}>
            {label}
          </option>
        ))}
      </Select>
    </label>
  );
}
