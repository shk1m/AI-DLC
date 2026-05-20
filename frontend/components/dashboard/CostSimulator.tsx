'use client';

/**
 * FE-05 — CostSimulator (Single-Screen Compact)
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
    <BentoCard padding="sm" accent>
      <SectionHeader
        title="레시피 원가 시뮬레이션"
        description="식수 → 1인분 / 총원가"
        icon={<Calculator className="h-4 w-4" />}
        size="sm"
        trailing={
          <button
            type="button"
            onClick={() => toggleChat(true)}
            className="inline-flex items-center gap-1 rounded-full bg-brand-600 px-2 py-0.5 text-[10px] font-semibold text-white shadow-sm hover:bg-brand-700"
          >
            <Sparkles className="h-2.5 w-2.5" /> AI 추천
          </button>
        }
      />

      {/* 식수 + 요약 — 한 줄 */}
      <div className="mt-3 grid shrink-0 grid-cols-3 gap-1.5">
        <ServingsControl servings={servings} onChange={setServings} />
        <SummaryStat
          label="1인분"
          value={simulation ? formatKRW(simulation.costPerServing) : null}
          loading={simulating}
        />
        <SummaryStat
          label="총원가"
          value={simulation ? formatKRW(simulation.totalCost) : null}
          loading={simulating}
          accent
        />
      </div>

      {/* 레시피 카드 — flex-1, 자체 스크롤 */}
      <div className="scroll-thin mt-2.5 flex min-h-0 flex-1 flex-col gap-1 overflow-y-auto pr-1">
        {recipesLoading &&
          Array.from({ length: 3 }).map((_, i) => (
            <div
              key={i}
              className="flex shrink-0 items-center justify-between rounded-md border border-ink-100 bg-white p-2"
            >
              <div className="flex flex-col gap-1">
                <Skeleton className="h-3.5 w-20" />
                <Skeleton className="h-2.5 w-28" />
              </div>
              <Skeleton className="h-3.5 w-12" />
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
                  'group flex shrink-0 items-center justify-between rounded-md border bg-white p-2 text-left transition-all',
                  active
                    ? 'border-brand-400 shadow-sm ring-2 ring-brand-100'
                    : 'border-ink-100 hover:border-brand-300',
                )}
              >
                <div className="flex min-w-0 items-center gap-2">
                  <div
                    className={cn(
                      'flex h-7 w-7 shrink-0 items-center justify-center rounded-md',
                      active ? 'bg-brand-600 text-white' : 'bg-ink-100 text-ink-500',
                    )}
                  >
                    <ChefHat className="h-3.5 w-3.5" />
                  </div>
                  <div className="min-w-0">
                    <p className="truncate text-[12px] font-semibold text-ink-900">{r.name}</p>
                    <p className="truncate text-[10px] text-ink-400">
                      {r.cuisine} · {r.ingredients.length}개 재료
                    </p>
                  </div>
                </div>
                <div className="flex flex-col items-end leading-tight">
                  <span className="text-[12px] font-bold tabular-nums text-ink-900">
                    {formatKRW(r.costPerServing)}
                  </span>
                  <span className="text-[9px] text-ink-400">/ 1인분</span>
                </div>
              </button>
            );
          })}

        {/* 활성 레시피 breakdown — 컴팩트 */}
        {activeRecipe && simulation && !simulating && (
          <div className="mt-1 shrink-0 rounded-md border border-ink-100 bg-white p-2">
            <p className="mb-1 text-[9px] font-semibold uppercase tracking-wide text-ink-400">
              재료 분해 · {servings}인 기준
            </p>
            <div className="flex flex-col gap-0.5">
              {simulation.breakdown.map((b) => (
                <div
                  key={b.ingredientId}
                  className="grid grid-cols-[1fr_auto_auto] items-center gap-2 text-[11px]"
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
              <p className="mt-1.5 line-clamp-2 rounded bg-ink-50 px-2 py-1 text-[10px] leading-snug text-ink-600">
                <span className="font-semibold text-brand-700">AI · </span>
                {activeRecipe.rationale}
              </p>
            )}
          </div>
        )}
      </div>
    </BentoCard>
  );
}

// ─────────────────────────────────────────────────────────────────────────────

function ServingsControl({
  servings,
  onChange,
}: {
  servings: number;
  onChange: (v: number) => void;
}) {
  return (
    <div className="flex flex-col gap-0.5 rounded-md border border-ink-200 bg-white px-2 py-1">
      <span className="inline-flex items-center gap-0.5 text-[9px] font-semibold uppercase tracking-wide text-ink-400">
        <Users className="h-2.5 w-2.5" /> 식수
      </span>
      <div className="flex items-center justify-between">
        <button
          type="button"
          onClick={() => onChange(servings - 10)}
          className="flex h-5 w-5 items-center justify-center rounded border border-ink-200 text-ink-500 hover:border-brand-300 hover:text-brand-700"
        >
          <Minus className="h-2.5 w-2.5" />
        </button>
        <input
          type="number"
          value={servings}
          onChange={(e) => onChange(Number(e.target.value) || 1)}
          className="w-12 bg-transparent text-center text-[13px] font-bold tabular-nums text-ink-900 outline-none"
        />
        <button
          type="button"
          onClick={() => onChange(servings + 10)}
          className="flex h-5 w-5 items-center justify-center rounded border border-ink-200 text-ink-500 hover:border-brand-300 hover:text-brand-700"
        >
          <Plus className="h-2.5 w-2.5" />
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
        'flex flex-col gap-0.5 rounded-md border bg-white px-2 py-1',
        accent ? 'border-brand-200 bg-gradient-to-br from-brand-50/60 to-white' : 'border-ink-200',
      )}
    >
      <span className="text-[9px] font-semibold uppercase tracking-wide text-ink-400">
        {label}
      </span>
      {loading ? (
        <Skeleton className="h-4 w-14" />
      ) : (
        <span
          className={cn(
            'truncate text-[13px] font-bold tabular-nums tracking-tight',
            accent ? 'text-brand-700' : 'text-ink-900',
          )}
        >
          {value ?? '—'}
        </span>
      )}
    </div>
  );
}
