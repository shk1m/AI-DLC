import path from 'path';
import { fileURLToPath } from 'url';

const __dirname = fileURLToPath(new URL('.', import.meta.url));

/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  // ECS/Docker 컨테이너 배포에 필요한 standalone 출력
  output: 'standalone',
  // 백엔드(FastAPI) 연동 시 NEXT_PUBLIC_API_BASE_URL 환경변수 사용
  env: {
    NEXT_PUBLIC_API_BASE_URL:
      process.env.NEXT_PUBLIC_API_BASE_URL ?? 'http://localhost:8000',
    NEXT_PUBLIC_USE_MOCK:
      process.env.NEXT_PUBLIC_USE_MOCK ?? 'true',
  },
  webpack: (config) => {
    // Docker 리눅스 환경에서도 @/ alias 가 동작하도록 명시
    config.resolve.alias = {
      ...config.resolve.alias,
      '@': path.resolve(__dirname, './'),
    };
    return config;
  },
};

export default nextConfig;
