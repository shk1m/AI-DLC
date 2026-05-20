'use client';

/**
 * FE-04 — PriceTable (Single-Screen Compact)
 */

import { ArrowDownRight, ArrowUpRight, Table as TableIcon } from 'lucide-react';

import { useAsync } from '@/lib/hooks';
import { fetchPriceSeries } from '@/lib/mockApi';
import { useDashboardStore } from '@/lib/store';
import { cn, formatKRW, formatRate, formatShortDate } from '@/lib/utils';

import { BentoCard } from '@/components/ui/BentoCard';
import { SectionHeader } from '@/components/ui/SectionHeader';
import { Skeleton } from '@/components/ui/SkeletonCard';

const RECENT_DAYS = 7;

export function PriceTable() {
  const selectedIngredientId = useDashboardStore((s) => s.selectedIngredientId);
  const focusedDate = useDashboardStore((s) => s.focusedDate);
  const setFocusedDate = useDashboardStore((s) => s.setFocusedDate);

  const { data: series, loading } = useAsync(
    () =>
      selectedIngredientId
        ? fetchPriceSeries({ ingredientId: selectedIngredientId })
        : Promise.resolve({
            ok: false as const,
            error: { code: 'NO_INGREDIENT', message: '재료를 선택하세요' },
            servedAt: new Date().toISOString(),
          }),
    [selectedIngredientId],
  );

  const recent = (series?.points ?? []).slice(-RECENT_DAYS).reverse();

  return (
    <BentoCard padding="sm">
      <SectionHeader
        title="최근 7일 도매 / 소매 / Gap"
        description={series ? `${series.ingredientName} (${series.unit})` : '일자별 시세 비교'}
        icon={<TableIcon className="h-4 w-4" />}
        size="sm"
      />

      <div className="mt-3 flex min-h-0 flex-1 flex-col">
        {/* 헤더 행 */}
        <div className="grid shrink-0 grid-cols-[56px_1fr_1fr_1fr_64px] items-center gap-2 border-b border-ink-100 px-2 pb-1.5 text-[10px] font-semibold uppercase tracking-wide text-ink-400">
          <span>날짜</span>
          <span className="text-right">도매</span>
          <span className="text-right">소매</span>
          <span className="text-right">Gap</span>
          <span className="text-right">변동</span>
        </div>

        <div className="scroll-thin flex min-h-0 flex-1 flex-col gap-0.5 overflow-y-auto pt-1">
          {loading &&
            Array.from({ length: 6 }).map((_, i) => (
              <div
                key={i}
                className="grid shrink-0 grid-cols-[56px_1fr_1fr_1fr_64px] items-center gap-2 px-2 py-1.5"
              >
                <Skeleton className="h-3.5 w-10" />
                <Skeleton className="h-3.5 w-14 justify-self-end" />
                <Skeleton className="h-3.5 w-14 justify-self-end" />
                <Skeleton className="h-3.5 w-10 justify-self-end" />
                <Skeleton className="h-3.5 w-8 justify-self-end" />
              </div>
            ))}

          {!loading &&
            recent.map((p) => {
              const focused = focusedDate === p.date;
              const isUp = (p.changeRate ?? 0) > 0;
              const isDown = (p.changeRate ?? 0) < 0;
              return (
                <button
                  key={p.date}
                  type="button"
                  onMouseEnter={() => setFocusedDate(p.date)}
                  onMouseLeave={() => setFocusedDate(null)}
                  onClick={() => setFocusedDate(p.date)}
                  className={cn(
                    'group relative grid shrink-0 grid-cols-[56px_1fr_1fr_1fr_64px] items-center gap-2 rounded-md px-2 py-1.5 text-left text-[12px] transition-all',
                    focused ? 'bg-brand-50' : 'hover:bg-ink-50',
                  )}
                >
                  {p.isSpike && (
                    <span
                      className={cn(
                        'absolute left-0 top-1/2 h-4 w-0.5 -translate-y-1/2 rounded-r-full',
                        p.spike?.direction === 'up' ? 'bg-spike-up' : 'bg-spike-down',
                      )}
                    />
                  )}
                  <span className="text-[11px] font-medium text-ink-600">
                    {formatShortDate(p.date)}
                  </span>
                  <span className="text-right font-semibold tabular-nums text-ink-900">
                    {formatKRW(p.wholesale)}
                  </span>
                  <span className="text-right tabular-nums text-ink-600">
                    {formatKRW(p.retail)}
                  </span>
                  <span className="text-right tabular-nums text-ink-500">
                    {formatKRW(p.gap)}
                  </span>
                  <span
                    className={cn(
                      'inline-flex items-center justify-end gap-0.5 text-right text-[11px] font-semibold tabular-nums',
                      isUp ? 'text-spike-up' : isDown ? 'text-spike-down' : 'text-ink-400',
                    )}
                  >
                    {isUp ? (
                      <ArrowUpRight className="h-2.5 w-2.5" />
                    ) : isDown ? (
                      <ArrowDownRight className="h-2.5 w-2.5" />
                    ) : null}
                    {formatRate(p.changeRate ?? 0)}
                  </span>
                </button>
              );
            })}

          {!loading && recent.length === 0 && (
            <div className="rounded-md border border-dashed border-ink-200 px-3 py-4 text-center text-[11px] text-ink-400">
              표시할 시세 데이터가 없습니다
            </div>
          )}
        </div>
      </div>
    </BentoCard>
  );
}
