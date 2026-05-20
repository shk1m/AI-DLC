'use client';

/**
 * ============================================================================
 *  Custom Hooks — 데이터 페칭 / 디바운스 / 기타 유틸
 * ----------------------------------------------------------------------------
 *  본 훅들은 mockApi 와 store 사이의 글루(glue) 코드입니다.
 *  실 백엔드 연동 시 mockApi 호출만 lib/api.ts 로 교체하면 컴포넌트 변경 없음.
 * ============================================================================
 */

import { useEffect, useRef, useState } from 'react';
import type { ApiResult } from '@/types';

interface AsyncState<T> {
  data: T | null;
  error: string | null;
  loading: boolean;
}

interface AsyncReturn<T> extends AsyncState<T> {
  refresh: () => void;
}

/**
 * 비동기 ApiResult fetcher 를 React state 로 노출.
 * deps 배열이 변경되면 자동 재페칭. unmount/재호출 시 race condition 방어.
 */
export function useAsync<T>(
  fn: () => Promise<ApiResult<T>>,
  deps: ReadonlyArray<unknown> = [],
): AsyncReturn<T> {
  const [state, setState] = useState<AsyncState<T>>({
    data: null,
    error: null,
    loading: true,
  });
  const [tick, setTick] = useState(0);

  // 최신 fn 참조 보관 (deps 외부에서 재계산되는 fn 도 안전하게)
  const fnRef = useRef(fn);
  fnRef.current = fn;

  useEffect(() => {
    let cancelled = false;
    setState((s) => ({ ...s, loading: true, error: null }));

    fnRef
      .current()
      .then((res) => {
        if (cancelled) return;
        if (res.ok) {
          setState({ data: res.data, error: null, loading: false });
        } else {
          setState({ data: null, error: res.error.message, loading: false });
        }
      })
      .catch((e: unknown) => {
        if (cancelled) return;
        const message = e instanceof Error ? e.message : 'Unknown error';
        setState({ data: null, error: message, loading: false });
      });

    return () => {
      cancelled = true;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [...deps, tick]);

  return { ...state, refresh: () => setTick((t) => t + 1) };
}

/**
 * 디바운스된 값 — 검색 인풋 등에 사용.
 */
export function useDebouncedValue<T>(value: T, delayMs = 300): T {
  const [debounced, setDebounced] = useState(value);

  useEffect(() => {
    const id = setTimeout(() => setDebounced(value), delayMs);
    return () => clearTimeout(id);
  }, [value, delayMs]);

  return debounced;
}
