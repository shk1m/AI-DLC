import type { Metadata } from 'next';
import './globals.css';

export const metadata: Metadata = {
  title: 'DLC — MD/영양사 AI 대시보드',
  description:
    'Data Lake Crew. 농수산물·가공식품 시세, 뉴스, 레시피 데이터를 결합한 급식 메뉴 단가 최적화 AI 대시보드.',
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="ko">
      <body>{children}</body>
    </html>
  );
}
