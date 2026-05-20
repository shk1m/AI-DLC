import { clsx, type ClassValue } from 'clsx';
import { twMerge } from 'tailwind-merge';

/** Tailwind class name merge helper */
export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

/** KRW currency 포맷 */
export function formatKRW(value: number): string {
  return new Intl.NumberFormat('ko-KR', {
    style: 'currency',
    currency: 'KRW',
    maximumFractionDigits: 0,
  }).format(value);
}

/** 변동률 포맷 (예: +3.2%, -1.8%) */
export function formatRate(rate: number): string {
  const sign = rate > 0 ? '+' : '';
  return `${sign}${rate.toFixed(1)}%`;
}

/** 짧은 날짜 포맷 (M.D) */
export function formatShortDate(iso: string): string {
  const d = new Date(iso);
  return `${d.getMonth() + 1}.${d.getDate()}`;
}

/** API 결과가 성공인지 판별 (타입 가드) */
export function isOk<T>(
  res: { ok: true; data: T } | { ok: false; error: { message: string } },
): res is { ok: true; data: T } {
  return res.ok === true;
}
