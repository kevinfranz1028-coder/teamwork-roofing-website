import type { Metadata } from 'next'
import { Inter } from 'next/font/google'
import './globals.css'
import Header from '@/components/Header'
import Footer from '@/components/Footer'
import MobileBottomBar from '@/components/MobileBottomBar'
import SchemaMarkup from '@/components/SchemaMarkup'

const inter = Inter({ subsets: ['latin'] })

export const metadata: Metadata = {
  title: 'Teamwork Roofing Services LLC | Kansas City Roofing & Exteriors',
  description: 'Roofing & Exteriors — Done The Teamwork Way. Serving Kansas City Metro with premium roofing, gutters, siding, and windows. Same-week inspections, photo-proof documentation, clean site guarantee.',
  keywords: 'roofing Kansas City, roof replacement, roof repair, gutters, siding, windows, storm damage, insurance claims, Kansas City Metro, KCK, KCMO, Johnson County',
  openGraph: {
    title: 'Teamwork Roofing Services LLC | Kansas City Roofing & Exteriors',
    description: 'Roofing & Exteriors — Done The Teamwork Way. Same-week inspections, photo-proof documentation, clean site guarantee.',
    url: 'https://teamworkroofing.com',
    siteName: 'Teamwork Roofing Services LLC',
    locale: 'en_US',
    type: 'website',
  },
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en">
      <head>
        <SchemaMarkup />
      </head>
      <body className={inter.className}>
        <Header />
        <main className="min-h-screen">
          {children}
        </main>
        <Footer />
        <MobileBottomBar />
      </body>
    </html>
  )
}
