import type { Config } from 'tailwindcss'

export default {
  content: ['./index.html', './src/**/*.{ts,tsx}'],
  theme: {
    extend: {
      colors: {
        border: 'hsl(var(--border))', input: 'hsl(var(--input))',
        ring: 'hsl(var(--ring))', background: 'hsl(var(--background))',
        foreground: 'hsl(var(--foreground))',
        primary: { DEFAULT: 'hsl(var(--primary))', foreground: 'hsl(var(--primary-foreground))' },
        secondary: { DEFAULT: 'hsl(var(--secondary))', foreground: 'hsl(var(--secondary-foreground))' },
        muted: { DEFAULT: 'hsl(var(--muted))', foreground: 'hsl(var(--muted-foreground))' },
        accent: { DEFAULT: 'hsl(var(--accent))', foreground: 'hsl(var(--accent-foreground))' },
        card: { DEFAULT: 'hsl(var(--card))', foreground: 'hsl(var(--card-foreground))' },
        destructive: { DEFAULT: 'hsl(var(--destructive))', foreground: 'hsl(var(--destructive-foreground))' },
      },
      borderRadius: {
        lg: 'var(--radius)', md: 'calc(var(--radius) - 2px)', sm: 'calc(var(--radius) - 4px)',
      },
      keyframes: {
        'bounce-small': {
          '0%, 100%': { transform: 'translateY(0)' },
          '50%': { transform: 'translateY(-4px)' },
        },
        walk: {
          '0%, 100%': { transform: 'translateY(0) rotate(0deg)' },
          '25%': { transform: 'translateY(-2px) rotate(-2deg)' },
          '75%': { transform: 'translateY(-2px) rotate(2deg)' },
        },
        jump: {
          '0%': { transform: 'translateY(0) scale(1, 1)' },
          '40%': { transform: 'translateY(-12px) scale(0.95, 1.05)' },
          '60%': { transform: 'translateY(-12px) scale(1.05, 0.95)' },
          '100%': { transform: 'translateY(0) scale(1, 1)' },
        },
        breathe: {
          '0%, 100%': { opacity: '1', transform: 'scale(1)' },
          '50%': { opacity: '0.5', transform: 'scale(0.75)' },
        },
      },
      animation: {
        'bounce-small': 'bounce-small 1.5s ease-in-out infinite',
        walk: 'walk 0.5s ease-in-out infinite',
        jump: 'jump 0.6s ease-in-out',
        breathe: 'breathe 1.8s ease-in-out infinite',
      },
    },
  },
  plugins: [],
} satisfies Config
