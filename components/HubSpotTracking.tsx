'use client'

import { useEffect } from 'react'
import { usePathname } from 'next/navigation'

/**
 * HubSpot SPA Route Change Tracking
 * Tracks virtual pageviews when users navigate between pages in Next.js
 */
export default function HubSpotTracking() {
  const pathname = usePathname()

  useEffect(() => {
    // Track route changes for SPA navigation
    if (typeof window !== 'undefined' && (window as any)._hsq) {
      const _hsq = (window as any)._hsq = (window as any)._hsq || []
      _hsq.push(['setPath', pathname])
      _hsq.push(['trackPageView'])
    }
  }, [pathname])

  return null
}
