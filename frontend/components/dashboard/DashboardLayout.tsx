'use client';

/**
 * FE-01 — DashboardLayout (Single Screen Grid)
 * ────────────────────────────────────────────────────────────────────────────
 *  ┌─────────────────────────────────────────────────────────────────────┐
 *  │  TopBar (56px)                                                      │
 *  ├──────────┬──────────────────────────┬──────────────────────────────┤
 *  │          │  PriceChart (1.55fr)     │  CostSimulator               │
 *  │ Category │                          │                              │
 *  │ Filter   ├──────────────────────────┼──────────────────────────────┤
 *  │ (full)   │  PriceTable (1fr)        │  SubstituteRecommender       │
 *  └──────────┴──────────────────────────┴──────────────────────────────┘
 *                                              [Floating ChatBot]
 *
 * 핵심: viewport 높이에 정확히 맞춤. 페이지 자체 스크롤 없음.
 *       각 카드가 grid cell 높이를 받고, 내부 콘텐츠는 카드 내에서 스크롤.
 * ────────────────────────────────────────────────────────────────────────────
 */

import { Activity, Database, Sparkles } from 'lucide-react';

import { CategoryFilter } from './CategoryFilter';
import { ChatBot } from './ChatBot';
import { CostSimulator } from './CostSimulator';
import { PriceChart } from './PriceChart';
import { PriceTable } from './PriceTable';
import { SubstituteRecommender } from './SubstituteRecommender';

export function DashboardLayout() {
  return (
    <div className="flex h-screen w-full flex-col">
      <TopBar />

      <main className="flex-1 min-h-0">
        <div className="one-screen-grid">
          <section className="area-filter">
            <CategoryFilter />
          </section>

          <section className="area-chart">
            <PriceChart />
          </section>

          <section className="area-sim">
            <CostSimulator />
          </section>

          <section className="area-table">
            <PriceTable />
          </section>

          <section className="area-sub">
            <SubstituteRecommender />
          </section>
        </div>
      </main>

      <ChatBot />
    </div>
  );
}

// ─────────────────────────────────────────────────────────────────────────────
// Top Bar (Slim, 56px)
// ─────────────────────────────────────────────────────────────────────────────

function TopBar() {
  return (
    <header
      className="sticky top-0 z-30 flex shrink-0 items-center justify-between border-b border-ink-100/60 bg-white/80 px-5 backdrop-blur-md"
      style={{ height: 'var(--topbar-h)' }}
    >
      <div className="flex items-center gap-2.5">
        <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-gradient-to-br from-brand-500 to-brand-700 text-white shadow-bento">
          <Sparkles className="h-3.5 w-3.5" />
        </div>
        <div className="leading-tight">
          <p className="text-[10px] font-semibold uppercase tracking-[0.18em] text-brand-600">
            Data Lake Crew
          </p>
          <h1 className="text-[13px] font-semibold tracking-tight text-ink-900">
            MD/영양사 AI 단가 최적화 대시보드
          </h1>
        </div>
      </div>

      <div className="flex items-center gap-2">
        <StatusPill icon={<Database className="h-3 w-3" />} label="Mock API" tone="warning" />
        <StatusPill icon={<Activity className="h-3 w-3" />} label="Live" tone="success" />
      </div>
    </header>
  );
}

function StatusPill({
  icon,
  label,
  tone,
}: {
  icon: React.ReactNode;
  label: string;
  tone: 'success' | 'warning' | 'neutral';
}) {
  const toneClass =
    tone === 'success'
      ? 'bg-brand-50 text-brand-700 ring-brand-200'
      : tone === 'warning'
        ? 'bg-amber-50 text-amber-700 ring-amber-200'
        : 'bg-ink-100 text-ink-600 ring-ink-200';

  return (
    <span
      className={`inline-flex items-center gap-1 rounded-full px-2 py-0.5 text-[10px] font-medium ring-1 ring-inset ${toneClass}`}
    >
      {icon}
      {label}
    </span>
  );
}
