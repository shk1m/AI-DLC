import { cn } from '@/lib/utils';
import type { HTMLAttributes, ReactNode } from 'react';

interface BentoCardProps extends HTMLAttributes<HTMLDivElement> {
  children: ReactNode;
  /** 강조 카드 (헤더 위쪽에 그라디언트 헤일로) */
  accent?: boolean;
  padding?: 'sm' | 'md' | 'lg';
}

export function BentoCard({
  children,
  className,
  accent,
  padding = 'md',
  ...rest
}: BentoCardProps) {
  return (
    <div
      className={cn(
        'group relative flex flex-col overflow-hidden rounded-bento border border-ink-100 bg-white shadow-bento transition-shadow duration-300 hover:shadow-bento-hover',
        padding === 'sm' && 'p-4',
        padding === 'md' && 'p-6',
        padding === 'lg' && 'p-8',
        accent &&
          'before:absolute before:inset-x-0 before:top-0 before:h-24 before:bg-gradient-to-b before:from-brand-50 before:to-transparent before:opacity-70 before:content-[""]',
        className,
      )}
      {...rest}
    >
      <div className="relative z-10 flex h-full flex-col">{children}</div>
    </div>
  );
}
