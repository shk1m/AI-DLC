import { cn } from '@/lib/utils';

interface SkeletonProps {
  className?: string;
}

/** 단일 스켈레톤 블록 (shimmer) */
export function Skeleton({ className }: SkeletonProps) {
  return (
    <div
      className={cn(
        'relative overflow-hidden rounded-md bg-ink-100',
        'before:absolute before:inset-0 before:-translate-x-full before:animate-shimmer',
        'before:bg-gradient-to-r before:from-transparent before:via-white/60 before:to-transparent',
        className,
      )}
    />
  );
}

interface SkeletonCardProps {
  /** 표시할 row 개수 */
  rows?: number;
  className?: string;
  showHeader?: boolean;
}

/** 카드 단위 스켈레톤 (헤더 + 줄들) */
export function SkeletonCard({ rows = 4, className, showHeader = true }: SkeletonCardProps) {
  return (
    <div className={cn('flex h-full flex-col gap-4', className)}>
      {showHeader && (
        <div className="flex items-center justify-between">
          <Skeleton className="h-5 w-32" />
          <Skeleton className="h-4 w-16" />
        </div>
      )}
      <div className="flex flex-col gap-3">
        {Array.from({ length: rows }).map((_, i) => (
          <Skeleton key={i} className={cn('h-4', i % 2 === 0 ? 'w-full' : 'w-5/6')} />
        ))}
      </div>
    </div>
  );
}
