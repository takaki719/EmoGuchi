import type { Metadata } from 'next'
import { Inter } from 'next/font/google'
import '@/styles/globals.css'

const inter = Inter({ subsets: ['latin'] })

export const metadata: Metadata = {
  title: 'EMOGUCHI - 音声演技感情推定ゲーム',
  description: 'リアルタイム音声演技と感情推定を楽しむパーティゲーム',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="ja">
      <body className={inter.className}>
        <main className="min-h-screen bg-gradient-to-br from-blue-50 to-purple-50">
          {children}
        </main>
      </body>
    </html>
  )
}