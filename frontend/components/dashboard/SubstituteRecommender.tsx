'use client';

/**
 * FE-07 — SubstituteRecommender (Single-Screen Compact)
 */

import { Beef, Lightbulb, Sparkles, Wand2 } from 'lucide-react';
import { useMemo } from 'react';

import { useAsync } from '@/lib/hooks';
import { fetchRecipes, fetchSubstitutes } from '@/lib/mockApi';
import { useDashboardStore } from '@/lib/store';
import { cn, formatKRW, formatRate } from '@/lib/utils';

import { BentoCard } from '@/components/ui/BentoCard';
import { SectionHeader } from '@/components/ui/SectionHeader';
import { Skeleton } from '@/components/ui/SkeletonCard';

export function SubstituteRecommender() {
  const activeRecipeId = useDashboardStore((s) => s.activeRecipeId);
  const selectedIngredientId = useDashboardStore((s) => s.selectedIngredientId);
  const setIngredient = useDashboardStore((s) => s.setIngredient);
  const toggleChat = useDashboardStore((s) => s.toggleChat);

  const { data: recipes } = useAsync(() => fetchRecipes({ limit: 20 }), []);

  const targetIngredientId = useMemo(() => {
    const recipe = recipes?.find((r) => r.id === activeRecipeId);
    if (!recipe || recipe.ingredients.length === 0) return selectedIngredientId;
    const sorted = [...recipe.ingredients].sort((a, b) => b.unitPrice - a.unitPrice);
    return sorted[0]?.ingredientId ?? selectedIngredientId;
  }, [recipes, activeRecipeId, selectedIngredientId]);

  const targetName = useMemo(() => {
    const recipe = recipes?.find((r) => r.id === activeRecipeId);
    return (
      recipe?.ingredients.find((i) => i.ingredientId === targetIngredientId)?.name ?? '선택 재료'
    );
  }, [recipes, activeRecipeId, targetIngredientId]);

  const { data: substitutes, loading } = useAsync(
    () =>
      targetIngredientId
        ? fetchSubstitutes(targetIngredientId)
        : Promise.resolve({
            ok: true as const,
            data: [],
            servedAt: new Date().toISOString(),
          }),
    [targetIngredientId],
  );

  return (
    <BentoCard padding="sm">
      <SectionHeader
        title="대체 식자재 추천"
        description={`${targetName} · 온톨로지+Bedrock`}
        icon={<Wand2 className="h-4 w-4" />}
        size="sm"
        trailing={
          substitutes && substitutes.length > 0 ? (
            <span className="rounded-full bg-brand-50 px-1.5 py-0.5 text-[9px] font-semibold text-brand-700">
              {substitutes.length}
            </span>
          ) : null
        }
      />

      <div className="scroll-thin mt-3 flex min-h-0 flex-1 flex-col gap-1.5 overflow-y-auto pr-1">
        {loading &&
          Array.from({ length: 2 }).map((_, i) => (
            <div
              key={i}
              className="flex shrink-0 items-center justify-between rounded-md border border-ink-100 bg-white p-2"
            >
              <div className="flex flex-col gap-1">
                <Skeleton className="h-3.5 w-16" />
                <Skeleton className="h-2.5 w-32" />
              </div>
              <div className="flex flex-col items-end gap-1">
                <Skeleton className="h-3.5 w-12" />
                <Skeleton className="h-2.5 w-8" />
              </div>
            </div>
          ))}

        {!loading && (substitutes?.length ?? 0) === 0 && (
          <div className="flex flex-1 flex-col items-center justify-center gap-1.5 rounded-md border border-dashed border-ink-200 px-3 py-4 text-center text-[11px] text-ink-400">
            <Lightbulb className="h-4 w-4 text-ink-300" />
            <span>
              현재 재료엔 우선 추천이 없어요.
              <br />
              가격 변동 큰 재료를 좌측에서 선택해 보세요.
            </span>
          </div>
        )}

        {!loading &&
          substitutes?.map((s) => (
            <article
              key={s.ingredient.id}
              className="group flex shrink-0 flex-col gap-1.5 rounded-md border border-ink-100 bg-white p-2 transition-all hover:border-brand-300"
            >
              <div className="flex items-start justify-between gap-2">
                <div className="flex items-center gap-1.5">
                  <div className="flex h-6 w-6 items-center justify-center rounded-md bg-brand-50 text-brand-600">
                    <Beef className="h-3 w-3" />
                  </div>
                  <div className="leading-tight">
                    <p className="text-[12px] font-semibold text-ink-900">{s.ingredient.name}</p>
                    <p className="text-[9px] text-ink-400">
                      Sim {Math.round(s.similarity * 100)}% · Q{' '}
                      {Math.round(s.qualityScore * 100)}%
                    </p>
                  </div>
                </div>
                <div className="flex flex-col items-end leading-tight">
                  <span className="text-[12px] font-bold tabular-nums text-spike-down">
                    -{formatKRW(s.savingPerServing)}
                  </span>
                  <span className="text-[9px] font-semibold text-spike-down">
                    {formatRate(-s.savingRate)}
                  </span>
                </div>
              </div>

              <p className="line-clamp-2 text-[10px] leading-snug text-ink-600">{s.rationale}</p>

              <div className="flex items-center justify-between">
                <ScoreBars similarity={s.similarity} quality={s.qualityScore} />
                <div className="flex gap-1">
                  <button
                    type="button"
                    onClick={() => setIngredient(s.ingredient.id)}
                    className="rounded border border-ink-200 bg-white px-1.5 py-0.5 text-[10px] font-semibold text-ink-700 hover:border-brand-300 hover:text-brand-700"
                  >
                    시세
                  </button>
                  <button
                    type="button"
                    onClick={() => toggleChat(true)}
                    className="inline-flex items-center gap-0.5 rounded bg-brand-600 px-1.5 py-0.5 text-[10px] font-semibold text-white hover:bg-brand-700"
                  >
                    <Sparkles className="h-2.5 w-2.5" /> 대화
                  </button>
                </div>
              </div>
            </article>
          ))}
      </div>
    </BentoCard>
  );
}

function ScoreBars({ similarity, quality }: { similarity: number; quality: number }) {
  return (
    <div className="flex items-center gap-1.5 text-[9px] text-ink-400">
      <Bar label="S" value={similarity} color="bg-brand-500" />
      <Bar label="Q" value={quality} color="bg-blue-500" />
    </div>
  );
}

function Bar({ label, value, color }: { label: string; value: number; color: string }) {
  return (
    <div className="flex items-center gap-0.5">
      <span className="font-semibold">{label}</span>
      <span className="relative inline-block h-1 w-8 overflow-hidden rounded-full bg-ink-100">
        <span
          className={cn('absolute inset-y-0 left-0 rounded-full', color)}
          style={{ width: `${Math.round(value * 100)}%` }}
        />
      </span>
    </div>
  );
}
