# ─────────────────────────────────────────────────────────────────
# Stage 1 — deps: 전체 의존성 설치 (devDeps 포함 — Next.js 빌드에 필요)
# ─────────────────────────────────────────────────────────────────
FROM node:18-alpine AS deps
RUN apk add --no-cache libc6-compat
WORKDIR /app

COPY package.json package-lock.json* ./
# devDependencies 포함 설치 (tailwindcss, typescript, eslint 등 빌드 필요)
RUN npm ci --no-audit --no-fund

# ─────────────────────────────────────────────────────────────────
# Stage 2 — builder: 프로덕션 빌드
# ─────────────────────────────────────────────────────────────────
FROM node:18-alpine AS builder
WORKDIR /app

COPY --from=deps /app/node_modules ./node_modules
COPY . .

# 빌드 시 Mock 모드 활성 (백엔드 없이 독립 배포)
ENV NEXT_PUBLIC_USE_MOCK=true
ENV NEXT_PUBLIC_API_BASE_URL=http://localhost:8000
ENV NEXT_TELEMETRY_DISABLED=1

RUN npm run build

# ─────────────────────────────────────────────────────────────────
# Stage 3 — runner: 최소 런타임 이미지
# devDeps 제외하고 standalone 결과물만 복사 → ~150MB
# ─────────────────────────────────────────────────────────────────
FROM node:18-alpine AS runner
WORKDIR /app

ENV NODE_ENV=production
ENV NEXT_TELEMETRY_DISABLED=1
ENV PORT=3000
ENV HOSTNAME=0.0.0.0

# 보안: non-root 사용자
RUN addgroup --system --gid 1001 nodejs \
 && adduser  --system --uid 1001 nextjs

# standalone 빌드 결과물만 복사 (devDeps 미포함)
COPY --from=builder /app/.next/standalone ./
COPY --from=builder /app/.next/static ./.next/static

USER nextjs

EXPOSE 3000
HEALTHCHECK --interval=30s --timeout=5s --start-period=15s --retries=3 \
  CMD wget -qO- http://localhost:3000/ || exit 1

CMD ["node", "server.js"]
