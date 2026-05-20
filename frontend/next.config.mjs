/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  // 백엔드(FastAPI) 연동 시 NEXT_PUBLIC_API_BASE_URL 환경변수 사용
  env: {
    NEXT_PUBLIC_API_BASE_URL:
      process.env.NEXT_PUBLIC_API_BASE_URL ?? 'http://localhost:8000',
    NEXT_PUBLIC_USE_MOCK:
      process.env.NEXT_PUBLIC_USE_MOCK ?? 'true',
  },
};

export default nextConfig;
