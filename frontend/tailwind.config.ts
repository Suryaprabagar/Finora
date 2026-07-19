import type { Config } from 'tailwindcss'

const config: Config = {
  content: [
    './src/pages/**/*.{js,ts,jsx,tsx,mdx}',
    './src/components/**/*.{js,ts,jsx,tsx,mdx}',
    './src/app/**/*.{js,ts,jsx,tsx,mdx}',
  ],
  darkMode: 'class',
  theme: {
    extend: {
      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'],
        display: ['Geist', 'system-ui', 'sans-serif'],
      },
      colors: {
        // Primary - Rich Brown
        primary: {
          DEFAULT: '#6f4627',
          container: '#8b5e3c',
          fixed: '#ffdcc5',
          'fixed-dim': '#f4bb92',
        },
        'on-primary': '#ffffff',
        'inverse-primary': '#f4bb92',
        // Secondary
        secondary: {
          DEFAULT: '#6b5c47',
          container: '#f5dfc4',
          fixed: '#f5dfc4',
          'fixed-dim': '#d8c4a9',
        },
        'on-secondary': '#ffffff',
        'on-secondary-container': '#241a0e',
        // Tertiary - Teal
        tertiary: {
          DEFAULT: '#265763',
          container: '#406f7c',
          fixed: '#baeaf9',
          'fixed-dim': '#9ecedd',
        },
        'on-tertiary': '#ffffff',
        // Background / Surface
        background: '#fff8f5',
        surface: {
          DEFAULT: '#fff8f5',
          bright: '#fff8f5',
          dim: '#e2d8d3',
          variant: '#ebe0db',
          'container-lowest': '#ffffff',
          'container-low': '#fcf1ec',
          container: '#f6ece7',
          'container-high': '#f1e6e1',
          'container-highest': '#ebe0db',
        },
        // Text
        'on-surface': '#1f1b18',
        'on-surface-variant': '#51443c',
        'on-background': '#1f1b18',
        outline: {
          DEFAULT: '#83746b',
          variant: '#d5c3b8',
        },
        // Error
        error: {
          DEFAULT: '#ba1a1a',
          container: '#ffdad6',
        },
        'on-error': '#ffffff',
        // Inverse
        'inverse-surface': '#352f2c',
        'inverse-on-surface': '#f9efe9',
        'surface-tint': '#805533',
      },
      borderRadius: {
        DEFAULT: '4px',
        sm: '6px',
        md: '8px',
        lg: '8px',
        xl: '12px',
        '2xl': '16px',
        full: '9999px',
      },
      boxShadow: {
        card: '0px 1px 3px rgba(0,0,0,0.02), 0px 4px 12px rgba(139,94,60,0.03)',
        'card-hover': '0px 2px 6px rgba(0,0,0,0.04), 0px 8px 24px rgba(139,94,60,0.06)',
        sm: '0 1px 2px rgba(0,0,0,0.04)',
      },
      spacing: {
        '18': '4.5rem',
        '22': '5.5rem',
        '60': '15rem',
        '68': '17rem',
      },
    },
  },
  plugins: [],
}
export default config
