'use client';

/**
 * FE-03 — CategoryFilter
 * ────────────────────────────────────────────────────────────────────────────
 * - 대분류 카테고리 탭 (mockApi.fetchCategories)
 * - 검색창 (디바운스 300ms, alias 포함)
 * - 하위 재료 리스트 (mockApi.fetchIngredients)
 * - Zustand 와 연동: 카테고리/재료 선택 시 차트/테이블/시뮬레이터/챗봇 컨텍스트 갱신
 * ────────────────────────────────────────────────────────────────────────────
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

// 아이콘 매핑 (mockData.icon 문자열 → Lucide 컴포넌트)
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

  // 1) 카테고리 목록
  const { data: categories, loading: catLoading } = useAsync(() => fetchCategories(), []);

  // 2) 재료 목록 (카테고리 + 검색어)
  const debouncedQuery = useDebouncedValue(ingredientQuery, 250);
  const {
    data: ingredientPage,
    loading: ingLoading,
  } = useAsync(
    () =>
      fetchIngredients({
        categoryId: selectedCategoryId ?? undefined,
        query: debouncedQuery || undefined,
        pageSize: 200,
      }),
    [selectedCategoryId, debouncedQuery],
  );

  const ingredients = useMemo(() => ingredientPage?.items ?? [], [ingredientPage]);

  // 카테고리 변경으로 재료가 사라졌으면 첫 항목 자동 선택
  useEffect(() => {
    if (ingLoading) return;
    if (!ingredients.length) return;
    const stillValid = ingredients.some((i) => i.id === selectedIngredientId);
    if (!stillValid) {
      setIngredient(ingredients[0]!.id);
    }
  }, [ingLoading, ingredients, selectedIngredientId, setIngredient]);

  return (
    <BentoCard className="min-h-[420px]" accent>
      <SectionHeader
        title="카테고리"
        description="대분류 → 재료 검색 / 선택"
        icon={<Tag className="h-4 w-4" />}
        trailing={
          <span className="text-[11px] font-medium text-ink-400">
            {ingredients.length}개 항목
          </span>
        }
      />

      {/* 카테고리 탭 */}
      <div className="mt-5 flex flex-wrap gap-2">
        {catLoading
          ? Array.from({ length: 4 }).map((_, i) => (
              <Skeleton key={i} className="h-7 w-16 rounded-full" />
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
                    'inline-flex items-center gap-1.5 rounded-full px-3 py-1.5 text-xs font-semibold transition-all',
                    active
                      ? 'bg-brand-600 text-white shadow-sm'
                      : 'border border-ink-200 bg-white text-ink-600 hover:border-brand-300 hover:text-brand-700',
                  )}
                >
                  <Icon className="h-3.5 w-3.5" />
                  {cat.name}
                </button>
              );
            })}
      </div>

      {/* 검색창 */}
      <label className="mt-3 flex items-center gap-2 rounded-lg border border-ink-200 bg-white px-3 py-2 focus-within:border-brand-400 focus-within:ring-2 focus-within:ring-brand-100">
        <Search className="h-4 w-4 text-ink-400" />
        <input
          type="text"
          value={ingredientQuery}
          onChange={(e) => setIngredientQuery(e.target.value)}
          placeholder="재료 검색 (예: 양파, onion)"
          className="w-full bg-transparent text-sm text-ink-700 outline-none placeholder:text-ink-400"
        />
      </label>

      {/* 재료 리스트 */}
      <div className="mt-3 flex max-h-[420px] min-h-0 flex-1 flex-col gap-1.5 overflow-y-auto pr-1">
        {ingLoading &&
          Array.from({ length: 6 }).map((_, i) => (
            <Skeleton key={i} className="h-9 w-full rounded-lg" />
          ))}
        {!ingLoading && ingredients.length === 0 && (
          <div className="flex flex-1 items-center justify-center rounded-lg border border-dashed border-ink-200 px-3 py-6 text-xs text-ink-400">
            검색 결과가 없습니다
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
                  'flex items-center justify-between rounded-lg border px-3 py-2 text-left text-sm transition-all',
                  active
                    ? 'border-brand-400 bg-brand-50/80 text-brand-800 shadow-sm'
                    : 'border-transparent bg-white text-ink-700 hover:border-ink-200 hover:bg-ink-50',
                )}
              >
                <span className="font-medium">{ing.name}</span>
                <span
                  className={cn(
                    'rounded-md px-1.5 py-0.5 text-[10px] font-semibold',
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
