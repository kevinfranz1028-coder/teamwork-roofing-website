import { MetadataRoute } from 'next'

export default function robots(): MetadataRoute.Robots {
  // Get the current host from environment or default to production domain
  const isProduction = process.env.CF_PAGES_URL?.includes('teamworkroofingkc.com') ||
                       process.env.NEXT_PUBLIC_SITE_URL === 'https://teamworkroofingkc.com'

  // Block all robots on .pages.dev preview URLs
  if (process.env.CF_PAGES_URL?.includes('.pages.dev')) {
    return {
      rules: {
        userAgent: '*',
        disallow: '/',
      },
    }
  }

  // Allow all robots on production domain
  return {
    rules: {
      userAgent: '*',
      allow: '/',
    },
    sitemap: 'https://teamworkroofingkc.com/sitemap.xml',
  }
}
