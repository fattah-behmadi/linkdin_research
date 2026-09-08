import { Suspense } from 'react';

import { ProfileCardSkeleton } from '@/components/molecules/profile-card-skeleton';
import { ProfileSearchTemplate } from '@/components/templates/profile-search-template';

export default function SearchPage() {
  return (
    <Suspense fallback={<ProfileCardSkeleton />}>
      <ProfileSearchTemplate />
    </Suspense>
  );
}
