import type { Config } from 'tailwindcss';

const config: Config = {
  content: [
    './app/**/*.{ts,tsx}',
    './components/**/*.{ts,tsx}',
    './lib/**/*.{ts,tsx}',
  ],
  theme: {
    extend: {
      colors: {
        // DLC 브랜드 팔레트 - Bento-box 미니멀 톤
        brand: {
          50: '#eef9f3',
          100: '#d6f1e2',
          200: '#aee3c6',
          300: '#7ccfa3',
          400: '#48b67d',
          500: '#239d62',
          600: '#177e4d',
          700: '#136340',
          800: '#114f35',
          900: '#0e3f2c',
        },
        ink: {
          50: '#f7f8fa',
          100: '#eef0f4',
          200: '#dadfe6',
          300: '#b6bec9',
          400: '#8b95a2',
          500: '#65707d',
          600: '#4a5462',
          700: '#374049',
          800: '#232a32',
          900: '#11161c',
        },
        spike: {
          up: '#ef4444',
          down: '#3b82f6',
        },
      },
      boxShadow: {
        bento:
          '0 1px 2px 0 rgb(17 22 28 / 0.04), 0 8px 24px -6px rgb(17 22 28 / 0.08)',
        'bento-hover':
          '0 1px 2px 0 rgb(17 22 28 / 0.04), 0 16px 36px -10px rgb(17 22 28 / 0.14)',
      },
      borderRadius: {
        bento: '20px',
      },
      fontFamily: {
        sans: [
          'Pretendard',
          'ui-sans-serif',
          'system-ui',
          '-apple-system',
          'Segoe UI',
          'Roboto',
          'sans-serif',
        ],
      },
      keyframes: {
        'fade-in': {
          '0%': { opacity: '0', transform: 'translateY(4px)' },
          '100%': { opacity: '1', transform: 'translateY(0)' },
        },
        'pulse-soft': {
          '0%, 100%': { opacity: '1' },
          '50%': { opacity: '0.55' },
        },
        shimmer: {
          '0%': { backgroundPosition: '-468px 0' },
          '100%': { backgroundPosition: '468px 0' },
        },
      },
      animation: {
        'fade-in': 'fade-in 200ms ease-out',
        'pulse-soft': 'pulse-soft 1.6s ease-in-out infinite',
        shimmer: 'shimmer 1.4s linear infinite',
      },
    },
  },
  plugins: [],
};

export default config;
