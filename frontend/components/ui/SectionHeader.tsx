import { cn } from '@/lib/utils';
import type { ReactNode } from 'react';

interface SectionHeaderProps {
  title: string;
  description?: string;
  icon?: ReactNode;
  /** 헤더 우측 액션 영역 (탭, 버튼 등) */
  trailing?: ReactNode;
  className?: string;
  size?: 'sm' | 'md';
}

export function SectionHeader({
  title,
  description,
  icon,
  trailing,
  className,
  size = 'md',
}: SectionHeaderProps) {
  return (
    <div className={cn('flex items-start justify-between gap-3', className)}>
      <div className="flex min-w-0 items-start gap-3">
        {icon && (
          <div
            className={cn(
              'flex shrink-0 items-center justify-center rounded-lg bg-brand-50 text-brand-600',
              size === 'sm' ? 'h-7 w-7' : 'h-9 w-9',
            )}
          >
            {icon}
          </div>
        )}
        <div className="min-w-0">
          <h3
            className={cn(
              'truncate font-semibold tracking-tight text-ink-900',
              size === 'sm' ? 'text-sm' : 'text-base',
            )}
          >
            {title}
          </h3>
          {description && (
            <p className="mt-0.5 line-clamp-2 text-xs text-ink-500">{description}</p>
          )}
        </div>
      </div>
      {trailing && <div className="shrink-0">{trailing}</div>}
    </div>
  );
}
