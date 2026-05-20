'use client';

/**
 * FE-03 — CategoryFilter (Single-Screen Compact)
 * - 좌측 컬럼 전체 높이 사용
 * - 헤더 + 탭(가로 스크롤) + 검색 + 재료 리스트(flex-1, 자체 스크롤)
 */

import { Beef, Fish, Package, Search, Sprout, Tag } from 'lucide-react';
import { useEffect, useMemo } from 'react';

import { useAsync, useDebouncedValue } from '@/lib/hooks';
import { fetchCategories, fetchIngredients } from '@/lib/mockApi';
import { useDashboardStore } from '@/lib/store';
import { cn } from '@/lib/utils';

import { BentoCard } from '@/components/ui/BentoCard';
import { SectionHeader } from '@/components/ui/SectionHeader';
import { Skeleton } from '@/components/ui/SkeletonCard';

const CATEGORY_ICONS: Record<string, React.ComponentType<{ className?: string }>> = {
  Sprout,
  Fish,
  Package,
  Beef,
};

export function CategoryFilter() {
  const selectedCategoryId = useDashboardStore((s) => s.selectedCategoryId);
  const selectedIngredientId = useDashboardStore((s) => s.selectedIngredientId);
  const ingredientQuery = useDashboardStore((s) => s.ingredientQuery);
  const setCategory = useDashboardStore((s) => s.setCategory);
  const setIngredient = useDashboardStore((s) => s.setIngredient);
  const setIngredientQuery = useDashboardStore((s) => s.setIngredientQuery);

  const { data: categories, loading: catLoading } = useAsync(() => fetchCategories(), []);

  const debouncedQuery = useDebouncedValue(ingredientQuery, 250);
  const { data: ingredientPage, loading: ingLoading } = useAsync(
    () =>
      fetchIngredients({
        categoryId: selectedCategoryId ?? undefined,
        query: debouncedQuery || undefined,
        pageSize: 200,
      }),
    [selectedCategoryId, debouncedQuery],
  );

  const ingredients = useMemo(() => ingredientPage?.items ?? [], [ingredientPage]);

  useEffect(() => {
    if (ingLoading) return;
    if (!ingredients.length) return;
    const stillValid = ingredients.some((i) => i.id === selectedIngredientId);
    if (!stillValid) {
      setIngredient(ingredients[0]!.id);
    }
  }, [ingLoading, ingredients, selectedIngredientId, setIngredient]);

  return (
    <BentoCard padding="sm" accent>
      <SectionHeader
        title="카테고리"
        description="대분류 → 재료 검색"
        icon={<Tag className="h-4 w-4" />}
        size="sm"
        trailing={
          <span className="rounded-full bg-ink-100 px-2 py-0.5 text-[10px] font-semibold text-ink-500">
            {ingredients.length}
          </span>
        }
      />

      {/* 카테고리 탭 — 가로 스크롤 가능 */}
      <div className="scroll-thin -mx-1 mt-3 flex shrink-0 gap-1.5 overflow-x-auto px-1 pb-1">
        {catLoading
          ? Array.from({ length: 4 }).map((_, i) => (
              <Skeleton key={i} className="h-6 w-14 shrink-0 rounded-full" />
            ))
          : categories?.map((cat) => {
              const Icon = (cat.icon && CATEGORY_ICONS[cat.icon]) || Tag;
              const active = cat.id === selectedCategoryId;
              return (
                <button
                  key={cat.id}
                  type="button"
                  onClick={() => setCategory(cat.id)}
                  className={cn(
                    'inline-flex shrink-0 items-center gap-1 rounded-full px-2.5 py-1 text-[11px] font-semibold transition-all',
                    active
                      ? 'bg-brand-600 text-white shadow-sm'
                      : 'border border-ink-200 bg-white text-ink-600 hover:border-brand-300 hover:text-brand-700',
                  )}
                >
                  <Icon className="h-3 w-3" />
                  {cat.name}
                </button>
              );
            })}
      </div>

      {/* 검색창 */}
      <label className="mt-2 flex shrink-0 items-center gap-1.5 rounded-md border border-ink-200 bg-white px-2.5 py-1.5 focus-within:border-brand-400 focus-within:ring-2 focus-within:ring-brand-100">
        <Search className="h-3.5 w-3.5 text-ink-400" />
        <input
          type="text"
          value={ingredientQuery}
          onChange={(e) => setIngredientQuery(e.target.value)}
          placeholder="재료 검색"
          className="w-full bg-transparent text-xs text-ink-700 outline-none placeholder:text-ink-400"
        />
      </label>

      {/* 재료 리스트 — flex-1, 자체 스크롤 */}
      <div className="scroll-thin mt-2 flex min-h-0 flex-1 flex-col gap-1 overflow-y-auto pr-1">
        {ingLoading &&
          Array.from({ length: 8 }).map((_, i) => (
            <Skeleton key={i} className="h-8 w-full shrink-0 rounded-md" />
          ))}
        {!ingLoading && ingredients.length === 0 && (
          <div className="flex flex-1 items-center justify-center rounded-md border border-dashed border-ink-200 px-2 py-4 text-[11px] text-ink-400">
            검색 결과 없음
          </div>
        )}
        {!ingLoading &&
          ingredients.map((ing) => {
            const active = ing.id === selectedIngredientId;
            return (
              <button
                key={ing.id}
                type="button"
                onClick={() => setIngredient(ing.id)}
                className={cn(
                  'flex shrink-0 items-center justify-between rounded-md border px-2.5 py-1.5 text-left text-xs transition-all',
                  active
                    ? 'border-brand-400 bg-brand-50/80 text-brand-800 shadow-sm'
                    : 'border-transparent bg-white text-ink-700 hover:border-ink-200 hover:bg-ink-50',
                )}
              >
                <span className="truncate font-medium">{ing.name}</span>
                <span
                  className={cn(
                    'ml-2 shrink-0 rounded px-1.5 py-0.5 text-[9px] font-semibold',
                    active ? 'bg-brand-600 text-white' : 'bg-ink-100 text-ink-500',
                  )}
                >
                  {ing.unit}
                </span>
              </button>
            );
          })}
      </div>
    </BentoCard>
  );
}
