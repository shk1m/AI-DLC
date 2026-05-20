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
    <div className={cn('flex shrink-0 items-start justify-between gap-2', className)}>
      <div className="flex min-w-0 items-center gap-2">
        {icon && (
          <div
            className={cn(
              'flex shrink-0 items-center justify-center rounded-md bg-brand-50 text-brand-600',
              size === 'sm' ? 'h-6 w-6' : 'h-8 w-8',
            )}
          >
            {icon}
          </div>
        )}
        <div className="min-w-0 leading-tight">
          <h3
            className={cn(
              'truncate font-semibold tracking-tight text-ink-900',
              size === 'sm' ? 'text-[13px]' : 'text-[15px]',
            )}
          >
            {title}
          </h3>
          {description && (
            <p
              className={cn(
                'truncate text-ink-500',
                size === 'sm' ? 'text-[10px]' : 'text-xs',
              )}
            >
              {description}
            </p>
          )}
        </div>
      </div>
      {trailing && <div className="shrink-0">{trailing}</div>}
    </div>
  );
}
