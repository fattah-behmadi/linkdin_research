import { Card, CardBody } from '@/components/atoms/card';
import { Skeleton } from '@/components/atoms/skeleton';

export function ProfileCardSkeleton() {
  return (
    <Card>
      <CardBody className="space-y-3">
        <Skeleton className="h-5 w-48" />
        <Skeleton className="h-4 w-72" />
        <div className="flex gap-2">
          <Skeleton className="h-5 w-16 rounded-full" />
          <Skeleton className="h-5 w-20 rounded-full" />
          <Skeleton className="h-5 w-24 rounded-full" />
        </div>
      </CardBody>
    </Card>
  );
}
