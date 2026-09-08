import type { Education, Experience, ProfileDetail } from '@/features/profiles/types';

function period(start: string | null, end: string | null, isCurrent = false): string {
  if (!start && !end) return '';
  return `${start ?? '?'} – ${isCurrent ? 'present' : (end ?? '?')}`;
}

function ExperienceRow({ item }: { item: Experience }) {
  return (
    <li className="border-border border-l-2 pl-3">
      <p className="text-sm font-medium capitalize">{item.title ?? 'Unknown role'}</p>
      <p className="text-muted-foreground text-sm capitalize">
        {[item.companyName, item.locationName].filter(Boolean).join(' · ')}
      </p>
      <p className="text-muted-foreground text-xs">
        {period(item.startDate, item.endDate, item.isCurrent)}
      </p>
    </li>
  );
}

function EducationRow({ item }: { item: Education }) {
  const study = [...item.degrees, ...item.majors].join(', ');
  return (
    <li className="border-border border-l-2 pl-3">
      <p className="text-sm font-medium capitalize">{item.schoolName ?? 'Unknown school'}</p>
      {study && <p className="text-muted-foreground text-sm capitalize">{study}</p>}
      <p className="text-muted-foreground text-xs">{period(item.startDate, item.endDate)}</p>
    </li>
  );
}

/** Presentational: everything `GET /profiles/{id}` adds on top of a search hit. */
export function ProfileDetailView({ profile }: { profile: ProfileDetail }) {
  return (
    <div className="grid gap-5 md:grid-cols-2">
      {profile.summary && (
        <section className="md:col-span-2">
          <h4 className="text-muted-foreground mb-1 text-xs font-semibold tracking-wide uppercase">
            Summary
          </h4>
          <p className="text-sm leading-relaxed">{profile.summary}</p>
        </section>
      )}

      <section>
        <h4 className="text-muted-foreground mb-2 text-xs font-semibold tracking-wide uppercase">
          Experience ({profile.experiences.length})
        </h4>
        {profile.experiences.length === 0 ? (
          <p className="text-muted-foreground text-sm">Not available</p>
        ) : (
          <ul className="space-y-3">
            {profile.experiences.slice(0, 6).map((item, index) => (
              <ExperienceRow key={`${item.companyName}-${item.startDate}-${index}`} item={item} />
            ))}
          </ul>
        )}
      </section>

      <section>
        <h4 className="text-muted-foreground mb-2 text-xs font-semibold tracking-wide uppercase">
          Education ({profile.educations.length})
        </h4>
        {profile.educations.length === 0 ? (
          <p className="text-muted-foreground text-sm">Not available</p>
        ) : (
          <ul className="space-y-3">
            {profile.educations.slice(0, 6).map((item, index) => (
              <EducationRow key={`${item.schoolName}-${index}`} item={item} />
            ))}
          </ul>
        )}
      </section>

      <section className="md:col-span-2">
        <h4 className="text-muted-foreground mb-2 text-xs font-semibold tracking-wide uppercase">
          All skills ({profile.skills.length})
        </h4>
        <p className="text-sm capitalize">{profile.skills.join(', ') || 'Not available'}</p>
      </section>
    </div>
  );
}
