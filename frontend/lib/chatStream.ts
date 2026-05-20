/**
 * ============================================================================
 *  Chat Stream — Bedrock 스트리밍 시뮬레이터
 * ----------------------------------------------------------------------------
 *  Mock 모드: 사용자 질문에 따라 적절한 Mock 답변 + 인라인 태그 + 인용을
 *  토큰 단위로 흘려보내는 AsyncIterable 을 반환.
 *
 *  실 모드 전환:
 *    - 동일 함수 시그니처로 lib/chatStreamWs.ts 작성
 *    - WebSocket → ChatStreamChunk 디코딩 → 동일 yield 구조
 *
 *  컴포넌트(ChatBot) 는 이 함수를 통해서만 메시지를 받습니다 (의존 역전).
 * ============================================================================
 */

import type { ChatCitation, ChatInlineTag, ChatStreamChunk } from '@/types';
import { INGREDIENTS, RECIPES } from './mockData';

interface AssistantPlan {
  text: string;
  inlineTags: ChatInlineTag[];
  citations: ChatCitation[];
}

/**
 * 사용자 질문 → mock 답변 플랜 매핑.
 * 실 모드에서는 Bedrock + Knowledge Base 가 이 역할을 대체.
 */
function planResponse(userText: string): AssistantPlan {
  const q = userText.toLowerCase();

  // 양파 가격 ─────────────────────────────────────────────────────────────
  if (/(양파|onion).*(왜|이유|급등|올|상승)/.test(userText) || q.includes('onion')) {
    return {
      text:
        '양파 도매가는 최근 30일 기준 약 18% 급등 구간이 한 차례 있었어요. 산지 폭우로 출하량이 30% 감소한 게 주된 원인입니다. 정부가 비축물량 1만톤 방출을 검토 중이라 단기 안정 가능성도 있습니다. 가격 부담이 큰 메뉴라면 대파를 30% 비율로 섞어 쓰는 방법을 권장드려요.',
      inlineTags: [
        { type: 'ingredient', label: '양파', refId: 'ing-onion' },
        { type: 'news', label: '비축물량 방출', refId: 'news-onion-2' },
      ],
      citations: [
        { title: '양파 산지 폭우 피해 확산', source: '농민신문', url: 'https://example.com/news/onion-1' },
        { title: '정부, 양파 비축물량 1만톤 시장 방출 검토', source: '농림축산식품부' },
      ],
    };
  }

  // 김치찌개 / 원가 ────────────────────────────────────────────────────────
  if (/(김치찌개|원가|단가).*(얼마|계산|시뮬)?/.test(userText) || userText.includes('김치찌개')) {
    return {
      text:
        '돼지고기 김치찌개의 1인분 예상 원가는 현재 시세 기준 약 ₩2,180입니다. 식수 200명 기준 ₩436,000 정도 들어요. 배추 가격이 22% 강세이지만 돼지고기·두부가 안정세라 전체 단가 영향은 제한적입니다. 배추 일부를 무로 대체하면 1인당 약 ₩240 절감할 수 있어요.',
      inlineTags: [
        { type: 'recipe', label: '김치찌개', refId: 'rcp-kimchi-jjigae' },
        { type: 'ingredient', label: '배추', refId: 'ing-cabbage' },
        { type: 'ingredient', label: '돼지고기', refId: 'ing-pork' },
      ],
      citations: [
        { title: '여름 배추 작황 부진… 김치업계 원가 부담 가중', source: '식품저널' },
      ],
    };
  }

  // 대체재 ─────────────────────────────────────────────────────────────────
  if (/(대체|대신|substitute)/.test(userText)) {
    return {
      text:
        '한우 등심이 8% 상승 구간이라면 같은 메뉴에서 돼지고기로 일부 대체하는 게 가장 무난합니다. 1인당 약 ₩3,675 절감되고, 양념 강도를 높이면 풍미 차이도 80% 정도 보완돼요. 닭고기는 절감폭은 더 크지만 풍미 차이가 커서 단기 임시 대응 메뉴에 권장합니다.',
      inlineTags: [
        { type: 'ingredient', label: '한우 등심', refId: 'ing-beef' },
        { type: 'ingredient', label: '돼지고기', refId: 'ing-pork' },
        { type: 'ingredient', label: '닭고기', refId: 'ing-chicken' },
      ],
      citations: [{ title: '온톨로지 기반 식자재 대체 추천', source: 'DLC Ontology v0.1' }],
    };
  }

  // 일반 — 가장 가까운 재료/레시피 매칭 시도
  const matchedIngredient = INGREDIENTS.find(
    (i) => userText.includes(i.name) || (i.aliases ?? []).some((a) => q.includes(a.toLowerCase())),
  );
  const matchedRecipe = RECIPES.find((r) => userText.includes(r.name));

  if (matchedIngredient) {
    return {
      text: `${matchedIngredient.name} 시세를 확인해 드릴게요. 좌측에서 ${matchedIngredient.name}을(를) 선택하시면 도매·소매 추이와 Spike 시점에 어떤 뉴스가 있었는지 차트에서 함께 보여드립니다. 1인분 원가나 대체 재료가 궁금하시면 바로 말씀해 주세요.`,
      inlineTags: [{ type: 'ingredient', label: matchedIngredient.name, refId: matchedIngredient.id }],
      citations: [],
    };
  }

  if (matchedRecipe) {
    return {
      text: `${matchedRecipe.name}의 1인분 예상 원가는 현재 ₩${matchedRecipe.costPerServing.toLocaleString()} 수준이에요. 식수에 따라 우측 시뮬레이터에서 즉시 계산되고, AI 유사 레시피 추천 버튼으로 더 저렴한 변형 메뉴도 받아볼 수 있습니다.`,
      inlineTags: [{ type: 'recipe', label: matchedRecipe.name, refId: matchedRecipe.id }],
      citations: [],
    };
  }

  return {
    text:
      '시세, 원가, 대체 재료 무엇이든 물어보세요. 예를 들어 "양파 가격이 왜 올랐어?" 또는 "김치찌개 200인분 원가 계산해줘" 같은 질문이 가능해요.',
    inlineTags: [
      { type: 'ingredient', label: '양파', refId: 'ing-onion' },
      { type: 'recipe', label: '김치찌개', refId: 'rcp-kimchi-jjigae' },
    ],
    citations: [],
  };
}

/**
 * 토큰 단위로 답변을 흘려보내는 AsyncIterable.
 * 실제 Bedrock 스트림처럼 구분자 단위로 잘라서 yield.
 */
export async function* streamMockChat(opts: {
  messageId: string;
  userText: string;
  /** 토큰 사이 지연(ms) */
  tokenDelay?: number;
}): AsyncGenerator<ChatStreamChunk, void, void> {
  const { messageId, userText, tokenDelay = 22 } = opts;
  const plan = planResponse(userText);

  // 한국어 자연 토큰 분할 (의미 단위에 가깝게)
  const tokens = plan.text.match(/.{1,3}/g) ?? [plan.text];

  for (const t of tokens) {
    await sleep(tokenDelay);
    yield { kind: 'token', messageId, delta: t };
  }

  // 인용은 토큰 후, 인라인 태그는 마지막에 일괄
  for (const c of plan.citations) {
    await sleep(60);
    yield { kind: 'citation', messageId, citation: c };
  }
  for (const tag of plan.inlineTags) {
    await sleep(40);
    yield { kind: 'inline_tag', messageId, tag };
  }

  await sleep(80);
  yield { kind: 'done', messageId };
}

function sleep(ms: number): Promise<void> {
  return new Promise((r) => setTimeout(r, ms));
}
