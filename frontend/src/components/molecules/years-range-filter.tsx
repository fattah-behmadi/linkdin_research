'use client';

import { Input } from '@/components/atoms/input';

interface YearsRangeFilterProps {
  min: number | null;
  max: number | null;
  onChange: (range: { minYears: number | null; maxYears: number | null }) => void;
}

function toValue(raw: string): number | null {
  const parsed = Number(raw);
  return raw.trim() === '' || !Number.isFinite(parsed) ? null : Math.max(0, Math.min(60, parsed));
}

/** Years of experience, as a numeric range. */
export function YearsRangeFilter({ min, max, onChange }: YearsRangeFilterProps) {
  return (
    <fieldset className="border-border border-t py-4">
      <legend className="mb-2 text-sm font-semibold">Years of experience</legend>
      <div className="flex items-center gap-2">
        <Input
          type="number"
          min={0}
          max={60}
          inputMode="numeric"
          aria-label="Minimum years of experience"
          placeholder="Min"
          value={min ?? ''}
          onChange={(event) => onChange({ minYears: toValue(event.target.value), maxYears: max })}
          className="h-9"
        />
        <span aria-hidden className="text-muted-foreground">
          –
        </span>
        <Input
          type="number"
          min={0}
          max={60}
          inputMode="numeric"
          aria-label="Maximum years of experience"
          placeholder="Max"
          value={max ?? ''}
          onChange={(event) => onChange({ minYears: min, maxYears: toValue(event.target.value) })}
          className="h-9"
        />
      </div>
    </fieldset>
  );
}
