'use client';

/**
 * FE-05 — CostSimulator
 * ────────────────────────────────────────────────────────────────────────────
 * - 식수(servings) 입력 (- / + / 직접)
 * - 레시피 카드 그리드 (활성 카드 강조)
 * - 활성 레시피의 breakdown (재료별 소계)
 * - 활성 레시피 변경 시 SubstituteRecommender 가 자동 갱신 (Zustand)
 * ────────────────────────────────────────────────────────────────────────────
 */

import { Calculator, ChefHat, Minus, Plus, Sparkles, Users } from 'lucide-react';

import { useAsync } from '@/lib/hooks';
import { fetchRecipes, simulateRecipeCost } from '@/lib/mockApi';
import { useDashboardStore } from '@/lib/store';
import { cn, formatKRW } from '@/lib/utils';

import { BentoCard } from '@/components/ui/BentoCard';
import { SectionHeader } from '@/components/ui/SectionHeader';
import { Skeleton } from '@/components/ui/SkeletonCard';

export function CostSimulator() {
  const selectedIngredientId = useDashboardStore((s) => s.selectedIngredientId);
  const activeRecipeId = useDashboardStore((s) => s.activeRecipeId);
  const servings = useDashboardStore((s) => s.servings);
  const setActiveRecipe = useDashboardStore((s) => s.setActiveRecipe);
  const setServings = useDashboardStore((s) => s.setServings);
  const toggleChat = useDashboardStore((s) => s.toggleChat);

  const { data: recipes, loading: recipesLoading } = useAsync(
    () => fetchRecipes({ contextIngredientId: selectedIngredientId ?? undefined, limit: 6 }),
    [selectedIngredientId],
  );

  const { data: simulation, loading: simulating } = useAsync(
    () =>
      activeRecipeId
        ? simulateRecipeCost({ recipeId: activeRecipeId, servings })
        : Promise.resolve({
            ok: false as const,
            error: { code: 'NO_RECIPE', message: '레시피를 선택하세요' },
            servedAt: new Date().toISOString(),
          }),
    [activeRecipeId, servings],
  );

  const activeRecipe = recipes?.find((r) => r.id === activeRecipeId);

  return (
    <BentoCard className="min-h-[300px]" accent>
      <SectionHeader
        title="레시피 원가 시뮬레이션"
        description="식수 입력 → 1인분 / 총 원가 즉시 계산"
        icon={<Calculator className="h-4 w-4" />}
        trailing={
          <button
            type="button"
            onClick={() => toggleChat(true)}
            className="inline-flex items-center gap-1 rounded-full bg-brand-600 px-2.5 py-1 text-[11px] font-semibold text-white shadow-sm hover:bg-brand-700"
          >
            <Sparkles className="h-3 w-3" /> AI 유사 레시피
          </button>
        }
      />

      {/* 식수 + 1인분 + 총원가 요약 */}
      <div className="mt-4 grid grid-cols-3 gap-2">
        <ServingsControl servings={servings} onChange={setServings} />
        <SummaryStat
          label="1인분"
          value={simulation ? formatKRW(simulation.costPerServing) : null}
          loading={simulating}
        />
        <SummaryStat
          label="총 원가"
          value={simulation ? formatKRW(simulation.totalCost) : null}
          loading={simulating}
          accent
        />
      </div>

      {/* 레시피 카드 */}
      <div className="mt-3 grid gap-2">
        {recipesLoading &&
          Array.from({ length: 3 }).map((_, i) => (
            <div
              key={i}
              className="flex items-center justify-between rounded-lg border border-ink-100 bg-white p-3"
            >
              <div className="flex flex-col gap-1.5">
                <Skeleton className="h-4 w-24" />
                <Skeleton className="h-3 w-32" />
              </div>
              <Skeleton className="h-4 w-16" />
            </div>
          ))}

        {!recipesLoading &&
          recipes?.map((r) => {
            const active = r.id === activeRecipeId;
            return (
              <button
                key={r.id}
                type="button"
                onClick={() => setActiveRecipe(r.id)}
                className={cn(
                  'group flex items-center justify-between rounded-lg border bg-white p-3 text-left transition-all',
                  active
                    ? 'border-brand-400 shadow-sm ring-2 ring-brand-100'
                    : 'border-ink-100 hover:border-brand-300',
                )}
              >
                <div className="flex min-w-0 items-center gap-2.5">
                  <div
                    className={cn(
                      'flex h-8 w-8 shrink-0 items-center justify-center rounded-lg',
                      active ? 'bg-brand-600 text-white' : 'bg-ink-100 text-ink-500',
                    )}
                  >
                    <ChefHat className="h-4 w-4" />
                  </div>
                  <div className="min-w-0">
                    <p className="truncate text-sm font-semibold text-ink-900">{r.name}</p>
                    <p className="truncate text-[11px] text-ink-400">
                      {r.cuisine} · {r.ingredients.length}개 재료
                    </p>
                  </div>
                </div>
                <div className="flex flex-col items-end">
                  <span className="text-sm font-bold tabular-nums text-ink-900">
                    {formatKRW(r.costPerServing)}
                  </span>
                  <span className="text-[10px] text-ink-400">/ 1인분</span>
                </div>
              </button>
            );
          })}
      </div>

      {/* 활성 레시피 breakdown */}
      {activeRecipe && simulation && !simulating && (
        <div className="mt-3 rounded-lg border border-ink-100 bg-white p-3">
          <p className="mb-2 text-[11px] font-semibold uppercase tracking-wide text-ink-400">
            재료 분해 · {servings}인 기준
          </p>
          <div className="flex flex-col gap-1">
            {simulation.breakdown.map((b) => (
              <div
                key={b.ingredientId}
                className="grid grid-cols-[1fr_auto_auto] items-center gap-2 text-xs"
              >
                <span className="truncate text-ink-700">{b.name}</span>
                <span className="text-right tabular-nums text-ink-400">
                  {b.quantity} {b.unit}
                </span>
                <span className="text-right font-semibold tabular-nums text-ink-900">
                  {formatKRW(b.subtotal)}
                </span>
              </div>
            ))}
          </div>
          {activeRecipe.rationale && (
            <p className="mt-2 line-clamp-2 rounded-md bg-ink-50 px-2.5 py-1.5 text-[11px] leading-snug text-ink-600">
              <span className="font-semibold text-brand-700">AI Insight · </span>
              {activeRecipe.rationale}
            </p>
          )}
        </div>
      )}
    </BentoCard>
  );
}

// ─────────────────────────────────────────────────────────────────────────────
// 보조 컴포넌트
// ─────────────────────────────────────────────────────────────────────────────

function ServingsControl({
  servings,
  onChange,
}: {
  servings: number;
  onChange: (v: number) => void;
}) {
  return (
    <div className="flex flex-col gap-1 rounded-lg border border-ink-200 bg-white px-3 py-2">
      <span className="inline-flex items-center gap-1 text-[11px] font-semibold uppercase tracking-wide text-ink-400">
        <Users className="h-3 w-3" /> 식수
      </span>
      <div className="flex items-center justify-between">
        <button
          type="button"
          onClick={() => onChange(servings - 10)}
          className="flex h-6 w-6 items-center justify-center rounded-md border border-ink-200 text-ink-500 hover:border-brand-300 hover:text-brand-700"
        >
          <Minus className="h-3 w-3" />
        </button>
        <input
          type="number"
          value={servings}
          onChange={(e) => onChange(Number(e.target.value) || 1)}
          className="w-14 bg-transparent text-center text-base font-bold tabular-nums text-ink-900 outline-none"
        />
        <button
          type="button"
          onClick={() => onChange(servings + 10)}
          className="flex h-6 w-6 items-center justify-center rounded-md border border-ink-200 text-ink-500 hover:border-brand-300 hover:text-brand-700"
        >
          <Plus className="h-3 w-3" />
        </button>
      </div>
    </div>
  );
}

function SummaryStat({
  label,
  value,
  loading,
  accent,
}: {
  label: string;
  value: string | null;
  loading?: boolean;
  accent?: boolean;
}) {
  return (
    <div
      className={cn(
        'flex flex-col gap-1 rounded-lg border bg-white px-3 py-2',
        accent ? 'border-brand-200 bg-gradient-to-br from-brand-50/60 to-white' : 'border-ink-200',
      )}
    >
      <span className="text-[11px] font-semibold uppercase tracking-wide text-ink-400">
        {label}
      </span>
      {loading ? (
        <Skeleton className="h-5 w-20" />
      ) : (
        <span
          className={cn(
            'text-base font-bold tabular-nums tracking-tight',
            accent ? 'text-brand-700' : 'text-ink-900',
          )}
        >
          {value ?? '—'}
        </span>
      )}
    </div>
  );
}
