'use client';

/**
 * FE-01 — DashboardLayout (Bento-box Skeleton)
 * ────────────────────────────────────────────────────────────────────────────
 * Single Page Unified Dashboard 의 최상위 레이아웃.
 *
 *   ┌──────────────────────────────────────────────────────────────────┐
 *   │  Top Bar: Brand · Range · Status · Profile                       │
 *   ├───────────────┬──────────────────────────┬───────────────────────┤
 *   │               │                          │                       │
 *   │  Category     │   PriceChart             │   CostSimulator       │
 *   │  Filter       │   (with CustomTooltip    │   (Recipe Cards)      │
 *   │  (FE-03)      │    + Spike markers)      │   (FE-05)             │
 *   │               │   (FE-02)                │                       │
 *   │               │                          │                       │
 *   │               ├──────────────────────────┤                       │
 *   │               │                          │   Substitute          │
 *   │               │   PriceTable             │   Recommender         │
 *   │               │   (FE-04)                │   (FE-07)             │
 *   │               │                          │                       │
 *   └───────────────┴──────────────────────────┴───────────────────────┘
 *                                                       Floating Chat (FE-06)
 *
 * 다른 컴포넌트는 Zustand store (`lib/store.ts`) 를 통해 상태를 공유합니다.
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
    <div className="min-h-screen w-full">
      <TopBar />

      <main className="mx-auto w-full max-w-[1480px] px-6 pb-16 pt-6">
        <div className="bento-grid">
          {/* 좌측 사이드 — CategoryFilter (FE-03) */}
          <section className="col-sidebar row-span-2">
            <CategoryFilter />
          </section>

          {/* 중앙 메인 — PriceChart (FE-02) */}
          <section className="col-main">
            <PriceChart />
          </section>

          {/* 우측 상단 — CostSimulator (FE-05) */}
          <section className="col-aside">
            <CostSimulator />
          </section>

          {/* 중앙 하단 — PriceTable (FE-04) */}
          <section className="col-main">
            <PriceTable />
          </section>

          {/* 우측 하단 — SubstituteRecommender (FE-07) */}
          <section className="col-aside">
            <SubstituteRecommender />
          </section>
        </div>
      </main>

      {/* 플로팅 — ChatBot (FE-06) */}
      <ChatBot />
    </div>
  );
}

// ─────────────────────────────────────────────────────────────────────────────
// Top Bar (Brand + Status)
// ─────────────────────────────────────────────────────────────────────────────

function TopBar() {
  return (
    <header className="sticky top-0 z-30 border-b border-ink-100/60 bg-white/70 backdrop-blur-md">
      <div className="mx-auto flex w-full max-w-[1480px] items-center justify-between px-6 py-3.5">
        <div className="flex items-center gap-3">
          <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-gradient-to-br from-brand-500 to-brand-700 text-white shadow-bento">
            <Sparkles className="h-4 w-4" />
          </div>
          <div className="leading-tight">
            <p className="text-[11px] font-semibold uppercase tracking-[0.18em] text-brand-600">
              Data Lake Crew
            </p>
            <h1 className="text-base font-semibold tracking-tight text-ink-900">
              MD/영양사 AI 단가 최적화 대시보드
            </h1>
          </div>
        </div>

        <div className="flex items-center gap-2">
          <StatusPill icon={<Database className="h-3.5 w-3.5" />} label="Mock API" tone="warning" />
          <StatusPill icon={<Activity className="h-3.5 w-3.5" />} label="Live" tone="success" />
        </div>
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
      className={`inline-flex items-center gap-1.5 rounded-full px-2.5 py-1 text-[11px] font-medium ring-1 ring-inset ${toneClass}`}
    >
      {icon}
      {label}
    </span>
  );
}
