'use client';

/**
 * FE-02 — PriceChart
 * ────────────────────────────────────────────────────────────────────────────
 * - mockApi.fetchPriceSeries(selectedIngredientId)
 * - Recharts LineChart (도매·소매 라인) + ReferenceDot (Spike)
 * - CustomTooltip 으로 일반 시점/Spike 시점 분기 렌더링 (뉴스 헤드라인 포함)
 * - KPI 미니카드 (현재가 / 평균 / 최저 / 최고 / 변동률 / Spike 횟수)
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

  // Spike 포인트만 추출 (ReferenceDot 용)
  const spikes = useMemo(() => points.filter((p) => p.isSpike), [points]);

  // Y축 도메인 (도매/소매 모두 커버)
  const yDomain = useMemo<[number, number] | undefined>(() => {
    if (points.length === 0) return undefined;
    const values = points.flatMap((p) => [p.wholesale, p.retail]);
    const min = Math.min(...values);
    const max = Math.max(...values);
    const pad = (max - min) * 0.15;
    return [Math.floor(min - pad), Math.ceil(max + pad)];
  }, [points]);

  return (
    <BentoCard className="min-h-[440px]">
      <SectionHeader
        title={series ? `${series.ingredientName} 시세 추이` : '시세 추이'}
        description="도매·소매. Spike 시점에 호버하면 관련 뉴스가 함께 표시됩니다."
        icon={<LineChartIcon className="h-4 w-4" />}
        trailing={<ChartLegend />}
      />

      {/* KPI 미니 카드 */}
      <div className="mt-5 grid grid-cols-2 gap-3 sm:grid-cols-4">
        <KpiCard
          label="현재가"
          value={summary ? formatKRW(summary.current) : null}
          subLabel={unit ? `/ ${unit}` : ''}
          loading={loading}
          accent
          deltaRate={summary?.changeRate}
        />
        <KpiCard
          label="구간 평균"
          value={summary ? formatKRW(summary.average) : null}
          subLabel={summary ? `${summary.range} 평균` : ''}
          loading={loading}
        />
        <KpiCard
          label="최저"
          value={summary ? formatKRW(summary.min) : null}
          subLabel="기간 내"
          loading={loading}
        />
        <KpiCard
          label="최고 / Spike"
          value={summary ? formatKRW(summary.max) : null}
          subLabel={summary ? `Spike ${summary.spikeCount}회` : ''}
          loading={loading}
          warning
        />
      </div>

      {/* 차트 영역 */}
      <div className="relative mt-4 flex-1">
        {loading && (
          <div className="absolute inset-0 flex items-center justify-center rounded-lg border border-dashed border-ink-200 bg-white/60">
            <Skeleton className="h-[260px] w-[95%]" />
          </div>
        )}

        {!loading && error && (
          <div className="flex h-full items-center justify-center rounded-lg border border-dashed border-red-200 bg-red-50/50 text-sm text-red-600">
            {error}
          </div>
        )}

        {!loading && !error && points.length > 0 && (
          <ResponsiveContainer width="100%" height="100%" minHeight={260}>
            <LineChart
              data={points}
              margin={{ top: 12, right: 12, left: 0, bottom: 4 }}
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
                tick={{ fontSize: 11, fill: '#8b95a2' }}
                stroke="#dadfe6"
                interval="preserveStartEnd"
                minTickGap={24}
              />
              <YAxis
                domain={yDomain ?? ['auto', 'auto']}
                tick={{ fontSize: 11, fill: '#8b95a2' }}
                stroke="#dadfe6"
                tickFormatter={(v: number) =>
                  v >= 10000 ? `${Math.round(v / 1000)}k` : `${v}`
                }
                width={48}
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

              {/* Spike 마커 */}
              {spikes.map((p) => (
                <ReferenceDot
                  key={p.date}
                  x={p.date}
                  y={p.wholesale}
                  r={6}
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
    <div className="flex items-center gap-3 text-[11px] text-ink-500">
      <span className="inline-flex items-center gap-1.5">
        <span className="inline-block h-0.5 w-4 rounded-full bg-brand-500" />
        도매
      </span>
      <span className="inline-flex items-center gap-1.5">
        <span className="inline-block h-0.5 w-4 rounded-full bg-blue-500" />
        소매
      </span>
      <span className="inline-flex items-center gap-1 text-spike-up">
        <Sparkles className="h-3 w-3" />
        Spike
      </span>
    </div>
  );
}

function KpiCard({
  label,
  value,
  subLabel,
  loading,
  accent,
  warning,
  deltaRate,
}: {
  label: string;
  value: string | null;
  subLabel?: string;
  loading?: boolean;
  accent?: boolean;
  warning?: boolean;
  deltaRate?: number;
}) {
  return (
    <div
      className={cn(
        'flex flex-col gap-1 rounded-lg border bg-white px-3 py-2.5',
        accent ? 'border-brand-200 bg-gradient-to-br from-brand-50/60 to-white' : 'border-ink-100',
        warning && 'border-amber-200 bg-gradient-to-br from-amber-50/60 to-white',
      )}
    >
      <span className="text-[11px] font-semibold uppercase tracking-wide text-ink-400">
        {label}
      </span>
      {loading ? (
        <Skeleton className="h-5 w-20" />
      ) : (
        <div className="flex items-baseline gap-1.5">
          <span className="text-base font-bold tabular-nums tracking-tight text-ink-900">
            {value ?? '—'}
          </span>
          {typeof deltaRate === 'number' && (
            <span
              className={cn(
                'inline-flex items-center gap-0.5 text-[11px] font-semibold',
                deltaRate > 0 ? 'text-spike-up' : deltaRate < 0 ? 'text-spike-down' : 'text-ink-400',
              )}
            >
              {deltaRate > 0 ? (
                <ArrowUpRight className="h-3 w-3" />
              ) : deltaRate < 0 ? (
                <ArrowDownRight className="h-3 w-3" />
              ) : null}
              {formatRate(deltaRate)}
            </span>
          )}
        </div>
      )}
      {subLabel && <span className="text-[10px] text-ink-400">{subLabel}</span>}
    </div>
  );
}
