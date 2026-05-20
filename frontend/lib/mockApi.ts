/**
 * ============================================================================
 *  Mock API Layer
 * ----------------------------------------------------------------------------
 *  실제 백엔드 연동 전, 동일한 시그니처로 화면을 테스트하기 위한 비동기 래퍼.
 *  모든 함수는 ApiResponse<T> 또는 ApiError 를 반환하며, 인공 latency 와
 *  옵션 에러 시뮬레이션을 포함합니다.
 *
 *  교체 전략 (Unit 4 Integration 팀):
 *    - `NEXT_PUBLIC_USE_MOCK=false` 일 때 `lib/api.ts`(실연동) 호출로 분기
 *    - 동일 함수 시그니처를 유지하므로 컴포넌트 코드 수정 최소화
 * ============================================================================
 */

import type {
  ApiError,
  ApiResponse,
  ApiResult,
  Category,
  CostSimulationResult,
  Ingredient,
  NewsItem,
  Paginated,
  PriceSeries,
  Recipe,
  Substitute,
} from '@/types';

import {
  CATEGORIES,
  INGREDIENTS,
  NEWS_POOL,
  PRICE_SERIES,
  RECIPES,
  SUBSTITUTES,
} from './mockData';

// ─────────────────────────────────────────────────────────────────────────────
// Helpers
// ─────────────────────────────────────────────────────────────────────────────

const MIN_LATENCY = 220;
const MAX_LATENCY = 720;

function randomLatency(): number {
  return MIN_LATENCY + Math.floor(Math.random() * (MAX_LATENCY - MIN_LATENCY));
}

function nowIso(): string {
  return new Date().toISOString();
}

function ok<T>(data: T, cache: 'hit' | 'miss' | 'stale' = 'miss'): ApiResponse<T> {
  return { ok: true, data, servedAt: nowIso(), cache };
}

function fail(code: string, message: string, details?: Record<string, unknown>): ApiError {
  return {
    ok: false,
    error: { code, message, details },
    servedAt: nowIso(),
  };
}

/**
 * 비동기 시뮬레이션 래퍼.
 * @param producer 실제 응답을 만드는 동기 함수
 * @param opts.failureRate 0~1, 무작위 실패 확률 (시연 안정성을 위해 0 권장)
 */
async function simulate<T>(
  producer: () => T | ApiError,
  opts?: { latencyMs?: number; failureRate?: number },
): Promise<ApiResult<T>> {
  const latency = opts?.latencyMs ?? randomLatency();
  await new Promise((r) => setTimeout(r, latency));

  if (opts?.failureRate && Math.random() < opts.failureRate) {
    return fail('MOCK_RANDOM_FAILURE', '시연용 무작위 실패 (재시도 가능)');
  }

  const result = producer();
  if (result && typeof result === 'object' && 'ok' in result && (result as ApiError).ok === false) {
    return result as ApiError;
  }
  return ok(result as T);
}

// ─────────────────────────────────────────────────────────────────────────────
// Categories
// ─────────────────────────────────────────────────────────────────────────────

export async function fetchCategories(): Promise<ApiResult<Category[]>> {
  return simulate(() => CATEGORIES);
}

// ─────────────────────────────────────────────────────────────────────────────
// Ingredients (검색/필터)
// ─────────────────────────────────────────────────────────────────────────────

export interface FetchIngredientsParams {
  categoryId?: string;
  query?: string;
  page?: number;
  pageSize?: number;
}

export async function fetchIngredients(
  params: FetchIngredientsParams = {},
): Promise<ApiResult<Paginated<Ingredient>>> {
  const { categoryId, query, page = 1, pageSize = 50 } = params;

  return simulate(() => {
    let filtered = INGREDIENTS;

    if (categoryId) {
      filtered = filtered.filter((i) => i.categoryId === categoryId);
    }

    if (query && query.trim()) {
      const q = query.trim().toLowerCase();
      filtered = filtered.filter((i) => {
        if (i.name.toLowerCase().includes(q)) return true;
        return (i.aliases ?? []).some((a) => a.toLowerCase().includes(q));
      });
    }

    const start = (page - 1) * pageSize;
    const items = filtered.slice(start, start + pageSize);

    return {
      items,
      total: filtered.length,
      page,
      pageSize,
    } as Paginated<Ingredient>;
  });
}

// ─────────────────────────────────────────────────────────────────────────────
// Price Series
// ─────────────────────────────────────────────────────────────────────────────

export interface FetchPriceSeriesParams {
  ingredientId: string;
  /** 일 단위 (예: 30, 90) */
  rangeDays?: number;
}

export async function fetchPriceSeries(
  params: FetchPriceSeriesParams,
): Promise<ApiResult<PriceSeries>> {
  return simulate(() => {
    const series = PRICE_SERIES[params.ingredientId];
    if (!series) {
      return fail('PRICE_SERIES_NOT_FOUND', `시세 데이터를 찾을 수 없습니다: ${params.ingredientId}`);
    }
    return series;
  });
}

// ─────────────────────────────────────────────────────────────────────────────
// News (Spike 호버 시 lazy fetch 가능)
// ─────────────────────────────────────────────────────────────────────────────

export async function fetchNewsForSpike(spikeId: string): Promise<ApiResult<NewsItem[]>> {
  return simulate(
    () => {
      // spike-{ingredientId}-{date}
      const parts = spikeId.split('-');
      // ingredientId 패턴은 'ing-xxx' 이므로 인덱스 1~2 결합
      const ingredientId = `${parts[1]}-${parts[2]}`;
      return NEWS_POOL[ingredientId] ?? [];
    },
    { latencyMs: 180 },
  );
}

// ─────────────────────────────────────────────────────────────────────────────
// Recipes
// ─────────────────────────────────────────────────────────────────────────────

export interface FetchRecipesParams {
  /** 추천 컨텍스트 — 현재 선택된 재료 ID (가격 변동 큰 재료 우선) */
  contextIngredientId?: string;
  limit?: number;
}

export async function fetchRecipes(
  params: FetchRecipesParams = {},
): Promise<ApiResult<Recipe[]>> {
  const { contextIngredientId, limit = 10 } = params;

  return simulate(() => {
    let recipes = [...RECIPES];

    // 컨텍스트 재료가 들어가는 레시피를 상단으로
    if (contextIngredientId) {
      recipes.sort((a, b) => {
        const aHas = a.ingredients.some((i) => i.ingredientId === contextIngredientId) ? 1 : 0;
        const bHas = b.ingredients.some((i) => i.ingredientId === contextIngredientId) ? 1 : 0;
        return bHas - aHas;
      });
    }

    return recipes.slice(0, limit);
  });
}

// ─────────────────────────────────────────────────────────────────────────────
// Cost Simulation
// ─────────────────────────────────────────────────────────────────────────────

export interface SimulateRecipeCostParams {
  recipeId: string;
  servings: number;
}

export async function simulateRecipeCost(
  params: SimulateRecipeCostParams,
): Promise<ApiResult<CostSimulationResult>> {
  return simulate(() => {
    const recipe = RECIPES.find((r) => r.id === params.recipeId);
    if (!recipe) {
      return fail('RECIPE_NOT_FOUND', `레시피를 찾을 수 없습니다: ${params.recipeId}`);
    }

    const breakdown = recipe.ingredients.map((ing) => {
      const totalQty = ing.quantityPerServing * params.servings;
      const subtotal = Math.round(totalQty * ing.unitPrice);
      return {
        ingredientId: ing.ingredientId,
        name: ing.name,
        quantity: Math.round(totalQty * 100) / 100,
        unit: ing.unit,
        unitPrice: ing.unitPrice,
        subtotal,
      };
    });

    const totalCost = breakdown.reduce((s, b) => s + b.subtotal, 0);
    const costPerServing = Math.round(totalCost / params.servings);

    return {
      recipeId: recipe.id,
      servings: params.servings,
      totalCost,
      costPerServing,
      breakdown,
      simulatedAt: nowIso(),
    } as CostSimulationResult;
  });
}

// ─────────────────────────────────────────────────────────────────────────────
// Substitute Recommendation (온톨로지 기반)
// ─────────────────────────────────────────────────────────────────────────────

export async function fetchSubstitutes(
  ingredientId: string,
): Promise<ApiResult<Substitute[]>> {
  return simulate(() => SUBSTITUTES[ingredientId] ?? [], { latencyMs: 540 });
}
