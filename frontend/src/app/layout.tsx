import type { Metadata } from 'next'
import './globals.css'
import { Providers } from '@/components/providers'
import { Toaster } from 'sonner'

export const metadata: Metadata = {
  title: {
    default: 'Finora — Where your financial future begins',
    template: '%s | Finora',
  },
  description:
    'Finora is a comprehensive personal finance management platform. Track income, expenses, investments, loans, and goals — all in one place.',
  keywords: ['personal finance', 'budget', 'investments', 'expense tracker', 'finora'],
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en">
      <head>
        <link rel="preconnect" href="https://fonts.googleapis.com" />
        <link rel="preconnect" href="https://fonts.gstatic.com" crossOrigin="anonymous" />
        <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600&family=Geist:wght@400;500;600;700;800&display=swap" rel="stylesheet" />
        <link href="https://fonts.googleapis.com/css2?family=Material+Symbols+Outlined:opsz,wght,FILL,GRAD@20..48,100..700,0..1,-50..200&display=block" rel="stylesheet" />
      </head>
      <body className="antialiased">
        <Providers>
          {children}
          <Toaster
            position="top-right"
            toastOptions={{
              style: {
                background: '#ffffff',
                border: '1px solid #E7E2DB',
                color: '#1f1b18',
                fontFamily: 'Inter, sans-serif',
                fontSize: '14px',
              },
            }}
          />
        </Providers>
      </body>
    </html>
  )
}
