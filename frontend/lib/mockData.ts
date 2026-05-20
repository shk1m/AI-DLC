/**
 * ============================================================================
 *  Mock Data Seed — Hackathon Demo
 * ----------------------------------------------------------------------------
 *  실제 백엔드(KAMIS / 공공데이터 / 네이버 / Bedrock) 연동 전 시연용 데이터.
 *  Unit 4 (Integration) 팀이 실데이터로 교체할 수 있도록 동일한 인터페이스
 *  (frontend/types/index.ts) 를 따릅니다.
 * ============================================================================
 */

import type {
  Category,
  Ingredient,
  NewsItem,
  PricePoint,
  PriceSeries,
  Recipe,
  Substitute,
} from '@/types';

// ─────────────────────────────────────────────────────────────────────────────
// Categories (대분류)
// ─────────────────────────────────────────────────────────────────────────────
export const CATEGORIES: Category[] = [
  { id: 'cat-agri', slug: 'agriculture', name: '농산물', icon: 'Sprout', subCategoryCount: 24 },
  { id: 'cat-fish', slug: 'fishery', name: '수산물', icon: 'Fish', subCategoryCount: 18 },
  { id: 'cat-proc', slug: 'processed', name: '가공식품', icon: 'Package', subCategoryCount: 32 },
  { id: 'cat-live', slug: 'livestock', name: '축산물', icon: 'Beef', subCategoryCount: 12 },
];

// ─────────────────────────────────────────────────────────────────────────────
// Ingredients (대표 품목)
// ─────────────────────────────────────────────────────────────────────────────
export const INGREDIENTS: Ingredient[] = [
  // 농산물
  { id: 'ing-onion', categoryId: 'cat-agri', name: '양파', aliases: ['onion'], unit: 'kg', ontologyNodeId: 'onto:agri/onion' },
  { id: 'ing-cabbage', categoryId: 'cat-agri', name: '배추', aliases: ['cabbage'], unit: '포기', ontologyNodeId: 'onto:agri/cabbage' },
  { id: 'ing-potato', categoryId: 'cat-agri', name: '감자', aliases: ['potato'], unit: 'kg', ontologyNodeId: 'onto:agri/potato' },
  { id: 'ing-spinach', categoryId: 'cat-agri', name: '시금치', aliases: ['spinach'], unit: 'kg', ontologyNodeId: 'onto:agri/spinach' },
  { id: 'ing-garlic', categoryId: 'cat-agri', name: '마늘', aliases: ['garlic'], unit: 'kg', ontologyNodeId: 'onto:agri/garlic' },
  { id: 'ing-pepper', categoryId: 'cat-agri', name: '청양고추', aliases: ['chili'], unit: 'kg', ontologyNodeId: 'onto:agri/chili' },

  // 수산물
  { id: 'ing-mackerel', categoryId: 'cat-fish', name: '고등어', aliases: ['mackerel'], unit: '마리', ontologyNodeId: 'onto:fish/mackerel' },
  { id: 'ing-squid', categoryId: 'cat-fish', name: '오징어', aliases: ['squid'], unit: '마리', ontologyNodeId: 'onto:fish/squid' },
  { id: 'ing-anchovy', categoryId: 'cat-fish', name: '멸치', aliases: ['anchovy'], unit: 'kg', ontologyNodeId: 'onto:fish/anchovy' },

  // 가공식품
  { id: 'ing-tofu', categoryId: 'cat-proc', name: '두부', aliases: ['tofu'], unit: '모', ontologyNodeId: 'onto:proc/tofu' },
  { id: 'ing-noodle', categoryId: 'cat-proc', name: '국수', aliases: ['noodle'], unit: 'kg', ontologyNodeId: 'onto:proc/noodle' },
  { id: 'ing-soy', categoryId: 'cat-proc', name: '간장', aliases: ['soy sauce'], unit: 'L', ontologyNodeId: 'onto:proc/soy' },

  // 축산물
  { id: 'ing-beef', categoryId: 'cat-live', name: '한우 등심', aliases: ['beef'], unit: 'kg', ontologyNodeId: 'onto:live/beef' },
  { id: 'ing-pork', categoryId: 'cat-live', name: '돼지고기', aliases: ['pork'], unit: 'kg', ontologyNodeId: 'onto:live/pork' },
  { id: 'ing-chicken', categoryId: 'cat-live', name: '닭고기', aliases: ['chicken'], unit: 'kg', ontologyNodeId: 'onto:live/chicken' },
];

// ─────────────────────────────────────────────────────────────────────────────
// News (Spike 이벤트와 매칭됨)
// ─────────────────────────────────────────────────────────────────────────────
export const NEWS_POOL: Record<string, NewsItem[]> = {
  'ing-onion': [
    {
      id: 'news-onion-1',
      title: '양파 산지 폭우 피해 확산… 출하량 30% 급감',
      source: '농민신문',
      publishedAt: '2026-05-08T01:20:00Z',
      url: 'https://example.com/news/onion-1',
      impactScore: 0.92,
      summary: '전남·경남 산지 폭우로 양파 출하 차질, 도매가 단기 급등 우려.',
      matchedKeywords: ['양파', '폭우', '산지', '출하'],
    },
    {
      id: 'news-onion-2',
      title: '정부, 양파 비축물량 1만톤 시장 방출 검토',
      source: '농림축산식품부',
      publishedAt: '2026-05-09T05:00:00Z',
      url: 'https://example.com/news/onion-2',
      impactScore: 0.78,
      summary: '가격 안정 위해 비축물량 조기 방출 추진.',
      matchedKeywords: ['양파', '비축', '방출', '가격안정'],
    },
  ],
  'ing-cabbage': [
    {
      id: 'news-cabbage-1',
      title: '여름 배추 작황 부진… 김치업계 원가 부담 가중',
      source: '식품저널',
      publishedAt: '2026-05-12T02:30:00Z',
      url: 'https://example.com/news/cabbage-1',
      impactScore: 0.85,
      summary: '강원도 고랭지 배추 정식 시기 지연으로 7월 가격 강세 전망.',
      matchedKeywords: ['배추', '고랭지', '김치', '원가'],
    },
  ],
  'ing-mackerel': [
    {
      id: 'news-mackerel-1',
      title: '고등어 어획량 회복… 도매가 안정세 진입',
      source: '수산경제',
      publishedAt: '2026-05-10T03:00:00Z',
      url: 'https://example.com/news/mackerel-1',
      impactScore: 0.7,
      summary: '제주 인근 어획량 증가로 가격 진정.',
      matchedKeywords: ['고등어', '어획량', '제주'],
    },
  ],
};

// ─────────────────────────────────────────────────────────────────────────────
// Price Series 생성기 (시연용 sin + 노이즈 + Spike 삽입)
// ─────────────────────────────────────────────────────────────────────────────
function generateSeries(opts: {
  ingredientId: string;
  ingredientName: string;
  unit: string;
  basePrice: number;
  days: number;
  spikeDates?: Array<{ offset: number; magnitude: number; direction: 'up' | 'down' }>;
}): PriceSeries {
  const { ingredientId, ingredientName, unit, basePrice, days, spikeDates = [] } = opts;
  const today = new Date('2026-05-20T00:00:00Z');

  const points: PricePoint[] = [];
  let prev = basePrice;

  for (let i = days - 1; i >= 0; i--) {
    const d = new Date(today);
    d.setUTCDate(today.getUTCDate() - i);
    const dateStr = d.toISOString().slice(0, 10);

    // 사인파 + 화이트노이즈
    const wave = Math.sin((days - i) / 6) * basePrice * 0.06;
    const noise = (Math.sin((days - i) * 1.7) + Math.cos((days - i) * 0.9)) * basePrice * 0.02;
    let wholesale = Math.round(basePrice + wave + noise);

    // Spike 삽입
    const spikeHit = spikeDates.find((s) => s.offset === i);
    let isSpike = false;
    if (spikeHit) {
      isSpike = true;
      const sign = spikeHit.direction === 'up' ? 1 : -1;
      wholesale = Math.round(wholesale * (1 + (spikeHit.magnitude / 100) * sign));
    }

    const retail = Math.round(wholesale * (1.18 + Math.random() * 0.05));
    const gap = retail - wholesale;
    const changeRate = prev === 0 ? 0 : Math.round(((wholesale - prev) / prev) * 1000) / 10;

    const point: PricePoint = {
      date: dateStr,
      wholesale,
      retail,
      gap,
      changeRate,
      isSpike,
    };

    if (isSpike && spikeHit) {
      point.spike = {
        id: `spike-${ingredientId}-${dateStr}`,
        date: dateStr,
        ingredientId,
        direction: spikeHit.direction,
        magnitude: spikeHit.magnitude,
        summary:
          spikeHit.direction === 'up'
            ? `${ingredientName} 가격 ${spikeHit.magnitude}% 급등 — 산지 공급 차질 영향`
            : `${ingredientName} 가격 ${spikeHit.magnitude}% 하락 — 출하량 회복`,
        keywords:
          spikeHit.direction === 'up'
            ? ['공급차질', '산지피해', '단기급등']
            : ['출하증가', '가격안정', '수급회복'],
        news: NEWS_POOL[ingredientId] ?? [],
      };
    }

    points.push(point);
    prev = wholesale;
  }

  const wholesales = points.map((p) => p.wholesale);
  const min = Math.min(...wholesales);
  const max = Math.max(...wholesales);
  const average = Math.round(wholesales.reduce((a, b) => a + b, 0) / wholesales.length);
  const current = points[points.length - 1]!.wholesale;
  const first = points[0]!.wholesale;
  const changeRate = Math.round(((current - first) / first) * 1000) / 10;
  const spikeCount = points.filter((p) => p.isSpike).length;

  return {
    ingredientId,
    ingredientName,
    unit,
    summary: {
      range: `${days}D`,
      current,
      average,
      min,
      max,
      changeRate,
      spikeCount,
    },
    points,
  };
}

export const PRICE_SERIES: Record<string, PriceSeries> = {
  'ing-onion': generateSeries({
    ingredientId: 'ing-onion',
    ingredientName: '양파',
    unit: 'kg',
    basePrice: 2400,
    days: 30,
    spikeDates: [
      { offset: 12, magnitude: 18, direction: 'up' },
      { offset: 5, magnitude: 9, direction: 'up' },
    ],
  }),
  'ing-cabbage': generateSeries({
    ingredientId: 'ing-cabbage',
    ingredientName: '배추',
    unit: '포기',
    basePrice: 4800,
    days: 30,
    spikeDates: [{ offset: 8, magnitude: 22, direction: 'up' }],
  }),
  'ing-potato': generateSeries({
    ingredientId: 'ing-potato',
    ingredientName: '감자',
    unit: 'kg',
    basePrice: 3200,
    days: 30,
  }),
  'ing-spinach': generateSeries({
    ingredientId: 'ing-spinach',
    ingredientName: '시금치',
    unit: 'kg',
    basePrice: 5400,
    days: 30,
    spikeDates: [{ offset: 15, magnitude: 12, direction: 'down' }],
  }),
  'ing-garlic': generateSeries({
    ingredientId: 'ing-garlic',
    ingredientName: '마늘',
    unit: 'kg',
    basePrice: 9800,
    days: 30,
  }),
  'ing-pepper': generateSeries({
    ingredientId: 'ing-pepper',
    ingredientName: '청양고추',
    unit: 'kg',
    basePrice: 14000,
    days: 30,
    spikeDates: [{ offset: 18, magnitude: 15, direction: 'up' }],
  }),
  'ing-mackerel': generateSeries({
    ingredientId: 'ing-mackerel',
    ingredientName: '고등어',
    unit: '마리',
    basePrice: 3800,
    days: 30,
    spikeDates: [{ offset: 10, magnitude: 14, direction: 'down' }],
  }),
  'ing-squid': generateSeries({
    ingredientId: 'ing-squid',
    ingredientName: '오징어',
    unit: '마리',
    basePrice: 4200,
    days: 30,
  }),
  'ing-anchovy': generateSeries({
    ingredientId: 'ing-anchovy',
    ingredientName: '멸치',
    unit: 'kg',
    basePrice: 18000,
    days: 30,
  }),
  'ing-tofu': generateSeries({
    ingredientId: 'ing-tofu',
    ingredientName: '두부',
    unit: '모',
    basePrice: 1800,
    days: 30,
  }),
  'ing-noodle': generateSeries({
    ingredientId: 'ing-noodle',
    ingredientName: '국수',
    unit: 'kg',
    basePrice: 2700,
    days: 30,
  }),
  'ing-soy': generateSeries({
    ingredientId: 'ing-soy',
    ingredientName: '간장',
    unit: 'L',
    basePrice: 6500,
    days: 30,
  }),
  'ing-beef': generateSeries({
    ingredientId: 'ing-beef',
    ingredientName: '한우 등심',
    unit: 'kg',
    basePrice: 92000,
    days: 30,
    spikeDates: [{ offset: 7, magnitude: 8, direction: 'up' }],
  }),
  'ing-pork': generateSeries({
    ingredientId: 'ing-pork',
    ingredientName: '돼지고기',
    unit: 'kg',
    basePrice: 18500,
    days: 30,
  }),
  'ing-chicken': generateSeries({
    ingredientId: 'ing-chicken',
    ingredientName: '닭고기',
    unit: 'kg',
    basePrice: 6200,
    days: 30,
  }),
};

// ─────────────────────────────────────────────────────────────────────────────
// Recipes (시뮬레이션 카드용)
// ─────────────────────────────────────────────────────────────────────────────
export const RECIPES: Recipe[] = [
  {
    id: 'rcp-kimchi-jjigae',
    name: '돼지고기 김치찌개',
    cuisine: '한식 백반',
    costPerServing: 2180,
    defaultServings: 200,
    confidence: 0.94,
    rationale: '제철 배추 가격 상승 구간이지만 돼지고기 안정세로 전체 단가 영향 제한적.',
    ingredients: [
      { ingredientId: 'ing-cabbage', name: '배추', quantityPerServing: 0.12, unit: '포기', unitPrice: 4800 },
      { ingredientId: 'ing-pork', name: '돼지고기', quantityPerServing: 0.05, unit: 'kg', unitPrice: 18500 },
      { ingredientId: 'ing-tofu', name: '두부', quantityPerServing: 0.25, unit: '모', unitPrice: 1800 },
      { ingredientId: 'ing-onion', name: '양파', quantityPerServing: 0.04, unit: 'kg', unitPrice: 2400 },
    ],
  },
  {
    id: 'rcp-bulgogi',
    name: '소불고기 정식',
    cuisine: '한식 정식',
    costPerServing: 5320,
    defaultServings: 200,
    confidence: 0.88,
    rationale: '한우 등심 8% 상승 영향. 호주산 등심 또는 안심으로 대체 시 18% 절감 가능.',
    ingredients: [
      { ingredientId: 'ing-beef', name: '한우 등심', quantityPerServing: 0.05, unit: 'kg', unitPrice: 92000 },
      { ingredientId: 'ing-onion', name: '양파', quantityPerServing: 0.06, unit: 'kg', unitPrice: 2400 },
      { ingredientId: 'ing-garlic', name: '마늘', quantityPerServing: 0.01, unit: 'kg', unitPrice: 9800 },
      { ingredientId: 'ing-soy', name: '간장', quantityPerServing: 0.02, unit: 'L', unitPrice: 6500 },
    ],
  },
  {
    id: 'rcp-godeungeo',
    name: '고등어구이 정식',
    cuisine: '한식 백반',
    costPerServing: 2640,
    defaultServings: 200,
    confidence: 0.91,
    rationale: '고등어 어획량 회복으로 가격 하락 구간. 메뉴 편성 적기.',
    ingredients: [
      { ingredientId: 'ing-mackerel', name: '고등어', quantityPerServing: 0.5, unit: '마리', unitPrice: 3800 },
      { ingredientId: 'ing-spinach', name: '시금치', quantityPerServing: 0.03, unit: 'kg', unitPrice: 5400 },
      { ingredientId: 'ing-garlic', name: '마늘', quantityPerServing: 0.005, unit: 'kg', unitPrice: 9800 },
    ],
  },
  {
    id: 'rcp-japchae',
    name: '잡채',
    cuisine: '한식 반찬',
    costPerServing: 1980,
    defaultServings: 200,
    confidence: 0.86,
    rationale: '시금치 12% 하락으로 단가 부담 완화.',
    ingredients: [
      { ingredientId: 'ing-noodle', name: '국수', quantityPerServing: 0.06, unit: 'kg', unitPrice: 2700 },
      { ingredientId: 'ing-spinach', name: '시금치', quantityPerServing: 0.04, unit: 'kg', unitPrice: 5400 },
      { ingredientId: 'ing-onion', name: '양파', quantityPerServing: 0.05, unit: 'kg', unitPrice: 2400 },
      { ingredientId: 'ing-pork', name: '돼지고기', quantityPerServing: 0.03, unit: 'kg', unitPrice: 18500 },
    ],
  },
];

// ─────────────────────────────────────────────────────────────────────────────
// Substitute (온톨로지 기반 — Mock)
// ─────────────────────────────────────────────────────────────────────────────
export const SUBSTITUTES: Record<string, Substitute[]> = {
  'ing-beef': [
    {
      ingredient: INGREDIENTS.find((i) => i.id === 'ing-pork')!,
      savingPerServing: 3675,
      savingRate: 69,
      similarity: 0.78,
      qualityScore: 0.82,
      rationale: '단백질·지방 조성 유사. 양념 간 강하게 가면 한우 풍미 80% 재현.',
    },
    {
      ingredient: INGREDIENTS.find((i) => i.id === 'ing-chicken')!,
      savingPerServing: 4290,
      savingRate: 81,
      similarity: 0.62,
      qualityScore: 0.71,
      rationale: '풍미 차이는 있으나 원가 부담 큰 메뉴 일시 대체에 적합.',
    },
  ],
  'ing-cabbage': [
    {
      ingredient: { id: 'ing-radish', categoryId: 'cat-agri', name: '무', unit: 'kg', ontologyNodeId: 'onto:agri/radish' },
      savingPerServing: 240,
      savingRate: 35,
      similarity: 0.71,
      qualityScore: 0.85,
      rationale: '국·찌개 베이스 식감 보완. 김치찌개 50% 비율 대체 권장.',
    },
  ],
  'ing-onion': [
    {
      ingredient: { id: 'ing-leek', categoryId: 'cat-agri', name: '대파', unit: 'kg', ontologyNodeId: 'onto:agri/leek' },
      savingPerServing: 96,
      savingRate: 22,
      similarity: 0.68,
      qualityScore: 0.79,
      rationale: '향미 유사. 볶음 요리 30% 비율 대체 가능.',
    },
  ],
};
