'use client';

/**
 * CustomTooltip — PriceChart 전용
 * ────────────────────────────────────────────────────────────────────────────
 * 일반 시점: 날짜 + 도매/소매/Gap 가격 + 변동률
 * Spike 시점: 위 정보 + spike summary + 키워드 칩 + 관련 뉴스 헤드라인 (최대 3건)
 * ────────────────────────────────────────────────────────────────────────────
 */

import { ArrowDownRight, ArrowUpRight, Newspaper, Sparkles } from 'lucide-react';
import type { TooltipProps } from 'recharts';
import type { NameType, ValueType } from 'recharts/types/component/DefaultTooltipContent';

import type { PricePoint } from '@/types';
import { cn, formatKRW, formatRate, formatShortDate } from '@/lib/utils';

type Props = TooltipProps<ValueType, NameType> & {
  unit: string;
};

export function PriceChartTooltip({ active, payload, unit }: Props) {
  if (!active || !payload || payload.length === 0) return null;

  // payload[0].payload 가 우리가 넣은 PricePoint
  const point = payload[0]?.payload as PricePoint | undefined;
  if (!point) return null;

  const isSpike = !!point.isSpike && !!point.spike;
  const direction = point.spike?.direction ?? 'up';

  return (
    <div
      className={cn(
        'pointer-events-none w-[300px] overflow-hidden rounded-xl border bg-white shadow-bento-hover',
        isSpike ? 'border-spike-up/60' : 'border-ink-100',
      )}
    >
      {/* 헤더: 날짜 + Spike 배지 */}
      <div
        className={cn(
          'flex items-center justify-between px-3.5 py-2.5 text-xs font-semibold',
          isSpike
            ? direction === 'up'
              ? 'bg-red-50 text-red-700'
              : 'bg-blue-50 text-blue-700'
            : 'bg-ink-50 text-ink-700',
        )}
      >
        <span className="tracking-tight">
          {new Date(point.date).toLocaleDateString('ko-KR', {
            year: 'numeric',
            month: 'long',
            day: 'numeric',
            weekday: 'short',
          })}
        </span>
        {isSpike && (
          <span className="inline-flex items-center gap-1 rounded-full bg-white/80 px-2 py-0.5 text-[10px] font-bold uppercase tracking-wide">
            <Sparkles className="h-3 w-3" />
            Spike {direction === 'up' ? '+' : '-'}
            {point.spike?.magnitude}%
          </span>
        )}
      </div>

      {/* 가격 정보 */}
      <div className="grid grid-cols-3 gap-2 px-3.5 py-3">
        <PriceCell label="도매" value={point.wholesale} unit={unit} accent />
        <PriceCell label="소매" value={point.retail} unit={unit} />
        <PriceCell label="Gap" value={point.gap} unit={unit} muted />
      </div>

      <div className="flex items-center justify-between border-t border-ink-100 px-3.5 py-2 text-[11px]">
        <span className="text-ink-500">전일 대비</span>
        <span
          className={cn(
            'inline-flex items-center gap-1 font-semibold',
            (point.changeRate ?? 0) > 0
              ? 'text-spike-up'
              : (point.changeRate ?? 0) < 0
                ? 'text-spike-down'
                : 'text-ink-500',
          )}
        >
          {(point.changeRate ?? 0) > 0 ? (
            <ArrowUpRight className="h-3 w-3" />
          ) : (point.changeRate ?? 0) < 0 ? (
            <ArrowDownRight className="h-3 w-3" />
          ) : null}
          {formatRate(point.changeRate ?? 0)}
        </span>
      </div>

      {/* Spike 상세 — 키워드 + 뉴스 */}
      {isSpike && point.spike && (
        <div className="border-t border-ink-100 bg-gradient-to-b from-white to-ink-50/40 px-3.5 py-3">
          <p className="line-clamp-2 text-[12px] font-semibold leading-snug text-ink-900">
            {point.spike.summary}
          </p>

          {point.spike.keywords.length > 0 && (
            <div className="mt-2 flex flex-wrap gap-1">
              {point.spike.keywords.map((kw) => (
                <span
                  key={kw}
                  className="rounded-full bg-ink-100 px-2 py-0.5 text-[10px] font-medium text-ink-600"
                >
                  #{kw}
                </span>
              ))}
            </div>
          )}

          {point.spike.news.length > 0 && (
            <div className="mt-2.5 flex flex-col gap-1.5">
              <div className="flex items-center gap-1 text-[10px] font-bold uppercase tracking-wide text-ink-400">
                <Newspaper className="h-3 w-3" />
                관련 뉴스
              </div>
              <ul className="flex flex-col gap-1">
                {point.spike.news.slice(0, 3).map((n) => (
                  <li
                    key={n.id}
                    className="flex items-start gap-1.5 text-[11px] leading-snug"
                  >
                    <span className="mt-1 h-1 w-1 shrink-0 rounded-full bg-spike-up" />
                    <span className="flex-1">
                      <span className="line-clamp-2 font-medium text-ink-800">
                        {n.title}
                      </span>
                      <span className="mt-0.5 block text-[10px] text-ink-400">
                        {n.source} · {formatShortDate(n.publishedAt)}
                      </span>
                    </span>
                  </li>
                ))}
              </ul>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

function PriceCell({
  label,
  value,
  unit,
  accent,
  muted,
}: {
  label: string;
  value: number;
  unit: string;
  accent?: boolean;
  muted?: boolean;
}) {
  return (
    <div className="flex flex-col gap-0.5">
      <span className="text-[10px] font-medium uppercase tracking-wide text-ink-400">
        {label}
      </span>
      <span
        className={cn(
          'text-[13px] font-bold tabular-nums leading-tight',
          accent ? 'text-brand-700' : muted ? 'text-ink-500' : 'text-ink-800',
        )}
      >
        {formatKRW(value)}
      </span>
      <span className="text-[10px] text-ink-400">/ {unit}</span>
    </div>
  );
}
