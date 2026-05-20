'use client';

/**
 * FE-02 — PriceChart (Single-Screen Compact)
 * ────────────────────────────────────────────────────────────────────────────
 * - Header (제목 + 범례)
 * - KPI strip — 가로 한 줄, 슬림
 * - LineChart — flex-1 로 남은 영역 모두 차지 (ResponsiveContainer 100%)
 * ────────────────────────────────────────────────────────────────────────────
 */

import { useMemo } from 'react';
import {
  CartesianGrid,
  Line,
  LineChart,
  ReferenceDot,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts';
import {
  ArrowDownRight,
  ArrowUpRight,
  LineChart as LineChartIcon,
  Sparkles,
} from 'lucide-react';

import { useAsync } from '@/lib/hooks';
import { fetchPriceSeries } from '@/lib/mockApi';
import { useDashboardStore } from '@/lib/store';
import { cn, formatKRW, formatRate, formatShortDate } from '@/lib/utils';

import { BentoCard } from '@/components/ui/BentoCard';
import { SectionHeader } from '@/components/ui/SectionHeader';
import { Skeleton } from '@/components/ui/SkeletonCard';
import { PriceChartTooltip } from './PriceChartTooltip';

export function PriceChart() {
  const selectedIngredientId = useDashboardStore((s) => s.selectedIngredientId);
  const setFocusedDate = useDashboardStore((s) => s.setFocusedDate);

  const { data: series, loading, error } = useAsync(
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

  const points = useMemo(() => series?.points ?? [], [series]);
  const summary = series?.summary;
  const unit = series?.unit ?? '';

  const spikes = useMemo(() => points.filter((p) => p.isSpike), [points]);

  const yDomain = useMemo<[number, number] | undefined>(() => {
    if (points.length === 0) return undefined;
    const values = points.flatMap((p) => [p.wholesale, p.retail]);
    const min = Math.min(...values);
    const max = Math.max(...values);
    const pad = (max - min) * 0.15;
    return [Math.floor(min - pad), Math.ceil(max + pad)];
  }, [points]);

  return (
    <BentoCard padding="sm">
      <SectionHeader
        title={series ? `${series.ingredientName} 시세 추이` : '시세 추이'}
        description="도매·소매 30일. Spike 지점에 호버하면 관련 뉴스가 표시됩니다."
        icon={<LineChartIcon className="h-4 w-4" />}
        size="sm"
        trailing={<ChartLegend />}
      />

      {/* KPI strip — 슬림한 가로 1줄 */}
      <div className="mt-3 grid shrink-0 grid-cols-4 gap-2">
        <KpiStat
          label="현재가"
          value={summary ? formatKRW(summary.current) : null}
          sub={unit ? `/ ${unit}` : ''}
          deltaRate={summary?.changeRate}
          loading={loading}
          accent
        />
        <KpiStat
          label="평균"
          value={summary ? formatKRW(summary.average) : null}
          sub={summary ? summary.range : ''}
          loading={loading}
        />
        <KpiStat
          label="최저"
          value={summary ? formatKRW(summary.min) : null}
          loading={loading}
        />
        <KpiStat
          label="최고"
          value={summary ? formatKRW(summary.max) : null}
          sub={summary ? `Spike ${summary.spikeCount}회` : ''}
          loading={loading}
          warning
        />
      </div>

      {/* 차트 영역 — flex-1 로 남은 공간 전부 사용 */}
      <div className="relative mt-3 min-h-0 flex-1">
        {loading && (
          <div className="absolute inset-0 flex items-center justify-center rounded-lg border border-dashed border-ink-200 bg-white/60">
            <Skeleton className="h-[80%] w-[95%]" />
          </div>
        )}

        {!loading && error && (
          <div className="flex h-full items-center justify-center rounded-lg border border-dashed border-red-200 bg-red-50/50 text-sm text-red-600">
            {error}
          </div>
        )}

        {!loading && !error && points.length > 0 && (
          <ResponsiveContainer width="100%" height="100%">
            <LineChart
              data={points}
              margin={{ top: 8, right: 8, left: 0, bottom: 0 }}
              onMouseMove={(state) => {
                const date = state?.activePayload?.[0]?.payload?.date as string | undefined;
                if (date) setFocusedDate(date);
              }}
              onMouseLeave={() => setFocusedDate(null)}
            >
              <defs>
                <linearGradient id="wholesaleStroke" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="0%" stopColor="#239d62" stopOpacity={1} />
                  <stop offset="100%" stopColor="#48b67d" stopOpacity={0.6} />
                </linearGradient>
              </defs>
              <CartesianGrid stroke="#eef0f4" vertical={false} strokeDasharray="3 3" />
              <XAxis
                dataKey="date"
                tickFormatter={formatShortDate}
                tick={{ fontSize: 10, fill: '#8b95a2' }}
                stroke="#dadfe6"
                interval="preserveStartEnd"
                minTickGap={28}
                tickMargin={6}
              />
              <YAxis
                domain={yDomain ?? ['auto', 'auto']}
                tick={{ fontSize: 10, fill: '#8b95a2' }}
                stroke="#dadfe6"
                tickFormatter={(v: number) =>
                  v >= 10000 ? `${Math.round(v / 1000)}k` : `${v}`
                }
                width={42}
              />
              <Tooltip
                cursor={{ stroke: '#b6bec9', strokeDasharray: '4 4' }}
                content={<PriceChartTooltip unit={unit} />}
                wrapperStyle={{ outline: 'none' }}
              />
              <Line
                type="monotone"
                dataKey="wholesale"
                name="도매"
                stroke="url(#wholesaleStroke)"
                strokeWidth={2.4}
                dot={false}
                activeDot={{ r: 4, fill: '#239d62', stroke: '#fff', strokeWidth: 2 }}
                isAnimationActive
                animationDuration={500}
              />
              <Line
                type="monotone"
                dataKey="retail"
                name="소매"
                stroke="#3b82f6"
                strokeWidth={1.6}
                strokeDasharray="4 4"
                dot={false}
                activeDot={{ r: 3.5, fill: '#3b82f6', stroke: '#fff', strokeWidth: 2 }}
                isAnimationActive
                animationDuration={500}
              />

              {spikes.map((p) => (
                <ReferenceDot
                  key={p.date}
                  x={p.date}
                  y={p.wholesale}
                  r={5}
                  fill={p.spike?.direction === 'up' ? '#ef4444' : '#3b82f6'}
                  stroke="#fff"
                  strokeWidth={2}
                  isFront
                />
              ))}
            </LineChart>
          </ResponsiveContainer>
        )}
      </div>
    </BentoCard>
  );
}

// ─────────────────────────────────────────────────────────────────────────────
// 보조 컴포넌트
// ─────────────────────────────────────────────────────────────────────────────

function ChartLegend() {
  return (
    <div className="flex items-center gap-2 text-[10px] text-ink-500">
      <span className="inline-flex items-center gap-1">
        <span className="inline-block h-0.5 w-3 rounded-full bg-brand-500" />
        도매
      </span>
      <span className="inline-flex items-center gap-1">
        <span className="inline-block h-0.5 w-3 rounded-full bg-blue-500" />
        소매
      </span>
      <span className="inline-flex items-center gap-0.5 text-spike-up">
        <Sparkles className="h-2.5 w-2.5" />
        Spike
      </span>
    </div>
  );
}

function KpiStat({
  label,
  value,
  sub,
  deltaRate,
  loading,
  accent,
  warning,
}: {
  label: string;
  value: string | null;
  sub?: string;
  deltaRate?: number;
  loading?: boolean;
  accent?: boolean;
  warning?: boolean;
}) {
  return (
    <div
      className={cn(
        'flex flex-col gap-0.5 rounded-md border px-2.5 py-1.5',
        accent
          ? 'border-brand-200 bg-gradient-to-br from-brand-50/60 to-white'
          : warning
            ? 'border-amber-200 bg-gradient-to-br from-amber-50/60 to-white'
            : 'border-ink-100 bg-white',
      )}
    >
      <span className="text-[10px] font-semibold uppercase tracking-wide text-ink-400">
        {label}
      </span>
      {loading ? (
        <Skeleton className="h-4 w-16" />
      ) : (
        <div className="flex items-baseline gap-1">
          <span className="truncate text-[13px] font-bold tabular-nums leading-tight tracking-tight text-ink-900">
            {value ?? '—'}
          </span>
          {typeof deltaRate === 'number' && (
            <span
              className={cn(
                'inline-flex shrink-0 items-center text-[10px] font-semibold',
                deltaRate > 0
                  ? 'text-spike-up'
                  : deltaRate < 0
                    ? 'text-spike-down'
                    : 'text-ink-400',
              )}
            >
              {deltaRate > 0 ? (
                <ArrowUpRight className="h-2.5 w-2.5" />
              ) : deltaRate < 0 ? (
                <ArrowDownRight className="h-2.5 w-2.5" />
              ) : null}
              {formatRate(deltaRate)}
            </span>
          )}
        </div>
      )}
      {sub && <span className="truncate text-[9px] text-ink-400">{sub}</span>}
    </div>
  );
}
