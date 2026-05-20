import { cn } from '@/lib/utils';
import type { HTMLAttributes, ReactNode } from 'react';

interface BentoCardProps extends HTMLAttributes<HTMLDivElement> {
  children: ReactNode;
  /** 강조 카드 (헤더 위쪽에 그라디언트 헤일로) */
  accent?: boolean;
  padding?: 'xs' | 'sm' | 'md' | 'lg';
}

export function BentoCard({
  children,
  className,
  accent,
  padding = 'sm',
  ...rest
}: BentoCardProps) {
  return (
    <div
      className={cn(
        // h-full + min-h-0 → grid cell 안에서 정확한 높이로 시집들 + 내부 스크롤 가능하게
        'group relative flex h-full min-h-0 flex-col overflow-hidden rounded-bento border border-ink-100 bg-white shadow-bento transition-shadow duration-300 hover:shadow-bento-hover',
        padding === 'xs' && 'p-3',
        padding === 'sm' && 'p-4',
        padding === 'md' && 'p-5',
        padding === 'lg' && 'p-6',
        accent &&
          'before:absolute before:inset-x-0 before:top-0 before:h-20 before:bg-gradient-to-b before:from-brand-50 before:to-transparent before:opacity-70 before:content-[""]',
        className,
      )}
      {...rest}
    >
      <div className="relative z-10 flex h-full min-h-0 flex-col">{children}</div>
    </div>
  );
}
