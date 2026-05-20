'use client';

/**
 * FE-04 — PriceTable
 * ────────────────────────────────────────────────────────────────────────────
 * - 선택된 재료의 최근 7일 도매/소매/Gap 시세
 * - 변동률 컬러링
 * - 호버/클릭 시 setFocusedDate (차트 cursor 와 동기화)
 * - Spike 행은 좌측 라인 강조
 * ────────────────────────────────────────────────────────────────────────────
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
    <BentoCard className="min-h-[280px]">
      <SectionHeader
        title="최근 7일 도매 / 소매 / Gap"
        description={
          series ? `${series.ingredientName} (${series.unit})` : '재료별 일자 시세 비교'
        }
        icon={<TableIcon className="h-4 w-4" />}
      />

      <div className="mt-4 flex flex-col">
        <div className="grid grid-cols-[80px_1fr_1fr_1fr_70px] items-center gap-2 px-3 py-2 text-[11px] font-semibold uppercase tracking-wide text-ink-400">
          <span>날짜</span>
          <span className="text-right">도매</span>
          <span className="text-right">소매</span>
          <span className="text-right">Gap</span>
          <span className="text-right">변동</span>
        </div>

        <div className="flex flex-col gap-1">
          {loading &&
            Array.from({ length: 6 }).map((_, i) => (
              <div
                key={i}
                className="grid grid-cols-[80px_1fr_1fr_1fr_70px] items-center gap-2 rounded-lg px-3 py-2"
              >
                <Skeleton className="h-4 w-12" />
                <Skeleton className="h-4 w-16 justify-self-end" />
                <Skeleton className="h-4 w-16 justify-self-end" />
                <Skeleton className="h-4 w-12 justify-self-end" />
                <Skeleton className="h-4 w-10 justify-self-end" />
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
                    'group relative grid grid-cols-[80px_1fr_1fr_1fr_70px] items-center gap-2 rounded-lg px-3 py-2 text-left text-sm transition-all',
                    focused ? 'bg-brand-50' : 'bg-white hover:bg-ink-50',
                  )}
                >
                  {p.isSpike && (
                    <span
                      className={cn(
                        'absolute left-0 top-1/2 h-6 w-1 -translate-y-1/2 rounded-r-full',
                        p.spike?.direction === 'up' ? 'bg-spike-up' : 'bg-spike-down',
                      )}
                    />
                  )}
                  <span className="text-xs font-medium text-ink-600">
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
                      'inline-flex items-center justify-end gap-0.5 text-right text-xs font-semibold tabular-nums',
                      isUp ? 'text-spike-up' : isDown ? 'text-spike-down' : 'text-ink-400',
                    )}
                  >
                    {isUp ? (
                      <ArrowUpRight className="h-3 w-3" />
                    ) : isDown ? (
                      <ArrowDownRight className="h-3 w-3" />
                    ) : null}
                    {formatRate(p.changeRate ?? 0)}
                  </span>
                </button>
              );
            })}

          {!loading && recent.length === 0 && (
            <div className="rounded-lg border border-dashed border-ink-200 px-3 py-6 text-center text-xs text-ink-400">
              표시할 시세 데이터가 없습니다
            </div>
          )}
        </div>
      </div>
    </BentoCard>
  );
}
