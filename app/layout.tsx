import type { Metadata } from 'next'
import { Open_Sans, Oswald } from 'next/font/google'
import Script from 'next/script'
import './globals.css'
import Header from '@/components/Header'
import Footer from '@/components/Footer'
import MobileBottomBar from '@/components/MobileBottomBar'
import SchemaMarkup from '@/components/SchemaMarkup'
import HubSpotTracking from '@/components/HubSpotTracking'

const openSans = Open_Sans({ subsets: ['latin'] })
const oswald = Oswald({ subsets: ['latin'], variable: '--font-heading' })

export const metadata: Metadata = {
  metadataBase: new URL('https://teamworkroofingkc.com'),
  title: 'Teamwork Roofing Services LLC | Kansas City Roofing & Exteriors',
  description: 'Built on Teamwork. Backed by Trust. Serving Kansas City Metro with premium roofing, gutters, siding, and windows. Same-week inspections, photo-proof documentation, clean site guarantee.',
  keywords: 'roofing Kansas City, roof replacement, roof repair, gutters, siding, windows, storm damage, insurance claims, Kansas City Metro, KCK, KCMO, Johnson County',
  openGraph: {
    title: 'Teamwork Roofing Services LLC | Kansas City Roofing & Exteriors',
    description: 'Built on Teamwork. Backed by Trust. Same-week inspections, photo-proof documentation, clean site guarantee.',
    url: 'https://teamworkroofingkc.com',
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
      <body className={`${openSans.className} ${oswald.variable}`}>
        {/* HubSpot Tracking Code - Site-Wide Analytics */}
        <Script
          id="hubspot-tracking"
          src="https://js-na2.hs-scripts.com/244741088.js"
          strategy="afterInteractive"
        />
        <HubSpotTracking />

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
