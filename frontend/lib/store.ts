/**
 * ============================================================================
 *  Global Store (Zustand)
 * ----------------------------------------------------------------------------
 *  Bento-box 컴포넌트 간 상호작용용 전역 상태.
 *  - 좌측 CategoryFilter 의 카테고리/재료 선택
 *  - PriceChart 의 hover/click 한 시점 (다른 카드의 컨텍스트로 전파)
 *  - CostSimulator 의 활성 레시피 (SubstituteRecommender 와 연동)
 *  - ChatBot 토글 + 대화 히스토리 (대화 컨텍스트는 선택 식자재/레시피와 연동)
 * ============================================================================
 */

import { create } from 'zustand';
import { devtools } from 'zustand/middleware';

import type { ChatCitation, ChatInlineTag, ChatMessage } from '@/types';

// ─────────────────────────────────────────────────────────────────────────────
// State 정의
// ─────────────────────────────────────────────────────────────────────────────

interface SelectionState {
  /** 좌측 탭에서 선택된 카테고리 */
  selectedCategoryId: string | null;
  /** 검색 키워드 (재료) */
  ingredientQuery: string;
  /** 차트/카드의 기준이 되는 재료 */
  selectedIngredientId: string | null;
  /** 차트에서 호버/클릭한 날짜 (ISO yyyy-mm-dd) */
  focusedDate: string | null;
  /** 시뮬레이터의 활성 레시피 */
  activeRecipeId: string | null;
  /** 시뮬레이터 식수 */
  servings: number;
}

interface ChatState {
  isChatOpen: boolean;
  chatMessages: ChatMessage[];
  /** 챗봇이 답변 중인지 */
  isChatStreaming: boolean;
}

interface DashboardActions {
  // selection
  setCategory: (categoryId: string | null) => void;
  setIngredientQuery: (q: string) => void;
  setIngredient: (ingredientId: string | null) => void;
  setFocusedDate: (date: string | null) => void;
  setActiveRecipe: (recipeId: string | null) => void;
  setServings: (servings: number) => void;

  // chat
  toggleChat: (open?: boolean) => void;
  appendChatMessage: (msg: ChatMessage) => void;
  appendChatToken: (messageId: string, delta: string) => void;
  appendChatInlineTag: (messageId: string, tag: ChatInlineTag) => void;
  appendChatCitation: (messageId: string, citation: ChatCitation) => void;
  finishChatStreaming: (messageId: string) => void;
  setChatStreaming: (v: boolean) => void;
  resetChat: () => void;
}

export type DashboardStore = SelectionState & ChatState & DashboardActions;

// ─────────────────────────────────────────────────────────────────────────────
// Initial state
// ─────────────────────────────────────────────────────────────────────────────

const INITIAL_SELECTION: SelectionState = {
  selectedCategoryId: 'cat-agri',
  ingredientQuery: '',
  selectedIngredientId: 'ing-onion',
  focusedDate: null,
  activeRecipeId: 'rcp-kimchi-jjigae',
  servings: 200,
};

const INITIAL_CHAT: ChatState = {
  isChatOpen: false,
  chatMessages: [
    {
      id: 'msg-welcome',
      role: 'assistant',
      content:
        '안녕하세요, MD/영양사 전용 AI 어시스턴트입니다. 식자재 시세, 레시피 원가, 대체 재료 추천을 도와드릴게요. 무엇을 알아볼까요?',
      createdAt: new Date().toISOString(),
      inlineTags: [
        { type: 'ingredient', label: '양파 시세', refId: 'ing-onion' },
        { type: 'recipe', label: '김치찌개 원가', refId: 'rcp-kimchi-jjigae' },
      ],
    },
  ],
  isChatStreaming: false,
};

// ─────────────────────────────────────────────────────────────────────────────
// Store
// ─────────────────────────────────────────────────────────────────────────────

export const useDashboardStore = create<DashboardStore>()(
  devtools(
    (set) => ({
      ...INITIAL_SELECTION,
      ...INITIAL_CHAT,

      // selection actions
      setCategory: (categoryId) =>
        set(
          (s) => ({
            selectedCategoryId: categoryId,
            // 카테고리 변경 시 재료 선택 리셋 (PriceChart가 자동으로 첫 항목을 선택)
            selectedIngredientId: categoryId === s.selectedCategoryId ? s.selectedIngredientId : null,
            focusedDate: null,
          }),
          false,
          'setCategory',
        ),
      setIngredientQuery: (q) => set({ ingredientQuery: q }, false, 'setIngredientQuery'),
      setIngredient: (ingredientId) =>
        set({ selectedIngredientId: ingredientId, focusedDate: null }, false, 'setIngredient'),
      setFocusedDate: (date) => set({ focusedDate: date }, false, 'setFocusedDate'),
      setActiveRecipe: (recipeId) => set({ activeRecipeId: recipeId }, false, 'setActiveRecipe'),
      setServings: (servings) =>
        set({ servings: Math.max(1, Math.floor(servings)) }, false, 'setServings'),

      // chat actions
      toggleChat: (open) =>
        set(
          (s) => ({ isChatOpen: typeof open === 'boolean' ? open : !s.isChatOpen }),
          false,
          'toggleChat',
        ),
      appendChatMessage: (msg) =>
        set((s) => ({ chatMessages: [...s.chatMessages, msg] }), false, 'appendChatMessage'),
      appendChatToken: (messageId, delta) =>
        set(
          (s) => ({
            chatMessages: s.chatMessages.map((m) =>
              m.id === messageId ? { ...m, content: m.content + delta } : m,
            ),
          }),
          false,
          'appendChatToken',
        ),
      appendChatInlineTag: (messageId, tag) =>
        set(
          (s) => ({
            chatMessages: s.chatMessages.map((m) =>
              m.id === messageId
                ? { ...m, inlineTags: [...(m.inlineTags ?? []), tag] }
                : m,
            ),
          }),
          false,
          'appendChatInlineTag',
        ),
      appendChatCitation: (messageId, citation) =>
        set(
          (s) => ({
            chatMessages: s.chatMessages.map((m) =>
              m.id === messageId
                ? { ...m, citations: [...(m.citations ?? []), citation] }
                : m,
            ),
          }),
          false,
          'appendChatCitation',
        ),
      finishChatStreaming: (messageId) =>
        set(
          (s) => ({
            isChatStreaming: false,
            chatMessages: s.chatMessages.map((m) =>
              m.id === messageId ? { ...m, isStreaming: false } : m,
            ),
          }),
          false,
          'finishChatStreaming',
        ),
      setChatStreaming: (v) => set({ isChatStreaming: v }, false, 'setChatStreaming'),
      resetChat: () => set({ ...INITIAL_CHAT }, false, 'resetChat'),
    }),
    { name: 'dlc-dashboard' },
  ),
);

// ─────────────────────────────────────────────────────────────────────────────
// Selectors (성능 최적화 — 컴포넌트별 필요한 슬라이스만 구독)
// ─────────────────────────────────────────────────────────────────────────────

export const selectSelection = (s: DashboardStore) => ({
  selectedCategoryId: s.selectedCategoryId,
  ingredientQuery: s.ingredientQuery,
  selectedIngredientId: s.selectedIngredientId,
  focusedDate: s.focusedDate,
  activeRecipeId: s.activeRecipeId,
  servings: s.servings,
});

export const selectChat = (s: DashboardStore) => ({
  isChatOpen: s.isChatOpen,
  chatMessages: s.chatMessages,
  isChatStreaming: s.isChatStreaming,
});
