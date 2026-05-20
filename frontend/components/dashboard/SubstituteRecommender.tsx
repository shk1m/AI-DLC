'use client';

/**
 * FE-07 — SubstituteRecommender
 * ────────────────────────────────────────────────────────────────────────────
 * - 활성 레시피의 재료 중 가격 변동이 가장 큰 재료를 자동 선택
 *   (없으면 selectedIngredientId 사용)
 * - mockApi.fetchSubstitutes 로 추천 결과 표시
 * - 카드별 절감액·절감률·유사도·품질 점수
 * - "이 재료로 대화하기" 버튼 → 챗봇 열기 + 컨텍스트 prompt
 * ────────────────────────────────────────────────────────────────────────────
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

  // 활성 레시피의 재료 중 단가가 가장 높은 재료를 우선 추천 대상으로 사용
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
    <BentoCard className="min-h-[260px]">
      <SectionHeader
        title="대체 식자재 추천"
        description={`${targetName} 기준 · 온톨로지 + Bedrock`}
        icon={<Wand2 className="h-4 w-4" />}
        trailing={
          substitutes && substitutes.length > 0 ? (
            <span className="rounded-full bg-brand-50 px-2 py-0.5 text-[10px] font-semibold text-brand-700">
              {substitutes.length}건
            </span>
          ) : null
        }
      />

      <div className="mt-4 flex flex-col gap-2">
        {loading &&
          Array.from({ length: 2 }).map((_, i) => (
            <div
              key={i}
              className="flex items-center justify-between rounded-lg border border-ink-100 bg-white p-3"
            >
              <div className="flex flex-col gap-1.5">
                <Skeleton className="h-4 w-20" />
                <Skeleton className="h-3 w-40" />
              </div>
              <div className="flex flex-col items-end gap-1">
                <Skeleton className="h-4 w-14" />
                <Skeleton className="h-3 w-10" />
              </div>
            </div>
          ))}

        {!loading && (substitutes?.length ?? 0) === 0 && (
          <div className="flex flex-col items-center justify-center gap-2 rounded-lg border border-dashed border-ink-200 px-3 py-6 text-center text-xs text-ink-400">
            <Lightbulb className="h-5 w-5 text-ink-300" />
            현재 재료에는 우선 추천이 없어요.
            <br />
            가격 변동이 큰 재료를 좌측에서 선택해 보세요.
          </div>
        )}

        {!loading &&
          substitutes?.map((s) => (
            <article
              key={s.ingredient.id}
              className="group flex flex-col gap-2 rounded-lg border border-ink-100 bg-white p-3 transition-all hover:border-brand-300"
            >
              <div className="flex items-start justify-between gap-2">
                <div className="flex items-center gap-2">
                  <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-brand-50 text-brand-600">
                    <Beef className="h-4 w-4" />
                  </div>
                  <div>
                    <p className="text-sm font-semibold text-ink-900">{s.ingredient.name}</p>
                    <p className="text-[11px] text-ink-400">
                      유사도 {Math.round(s.similarity * 100)}% · 품질{' '}
                      {Math.round(s.qualityScore * 100)}%
                    </p>
                  </div>
                </div>
                <div className="flex flex-col items-end leading-tight">
                  <span className="text-sm font-bold tabular-nums text-spike-down">
                    -{formatKRW(s.savingPerServing)}
                  </span>
                  <span className="text-[10px] font-semibold text-spike-down">
                    {formatRate(-s.savingRate)}
                  </span>
                </div>
              </div>

              <p className="line-clamp-2 text-[11px] leading-snug text-ink-600">{s.rationale}</p>

              <div className="flex items-center justify-between">
                <ScoreBars similarity={s.similarity} quality={s.qualityScore} />
                <div className="flex gap-1.5">
                  <button
                    type="button"
                    onClick={() => setIngredient(s.ingredient.id)}
                    className="rounded-md border border-ink-200 bg-white px-2 py-1 text-[11px] font-semibold text-ink-700 hover:border-brand-300 hover:text-brand-700"
                  >
                    시세 보기
                  </button>
                  <button
                    type="button"
                    onClick={() => toggleChat(true)}
                    className="inline-flex items-center gap-1 rounded-md bg-brand-600 px-2 py-1 text-[11px] font-semibold text-white hover:bg-brand-700"
                  >
                    <Sparkles className="h-3 w-3" /> 대화
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
    <div className="flex items-center gap-2 text-[10px] text-ink-400">
      <Bar label="Sim" value={similarity} color="bg-brand-500" />
      <Bar label="Q" value={quality} color="bg-blue-500" />
    </div>
  );
}

function Bar({ label, value, color }: { label: string; value: number; color: string }) {
  return (
    <div className="flex items-center gap-1">
      <span className="font-semibold">{label}</span>
      <span className="relative inline-block h-1 w-10 overflow-hidden rounded-full bg-ink-100">
        <span
          className={cn('absolute inset-y-0 left-0 rounded-full', color)}
          style={{ width: `${Math.round(value * 100)}%` }}
        />
      </span>
    </div>
  );
}
