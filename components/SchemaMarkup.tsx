export default function SchemaMarkup() {
  const schema = {
    '@context': 'https://schema.org',
    '@type': 'LocalBusiness',
    '@id': 'https://teamworkroofing.com',
    name: 'Teamwork Roofing Services LLC',
    image: 'https://teamworkroofing.com/logo.png',
    url: 'https://teamworkroofing.com',
    telephone: '+1-913-396-3717',
    priceRange: '$$',
    address: {
      '@type': 'PostalAddress',
      addressLocality: 'Kansas City',
      addressRegion: 'KS',
      addressCountry: 'US'
    },
    geo: {
      '@type': 'GeoCoordinates',
      latitude: 39.0997,
      longitude: -94.5786
    },
    areaServed: [
      {
        '@type': 'City',
        name: 'Kansas City',
        '@id': 'https://en.wikipedia.org/wiki/Kansas_City,_Missouri'
      },
      {
        '@type': 'City',
        name: 'Overland Park',
        '@id': 'https://en.wikipedia.org/wiki/Overland_Park,_Kansas'
      },
      {
        '@type': 'City',
        name: 'Olathe',
        '@id': 'https://en.wikipedia.org/wiki/Olathe,_Kansas'
      },
      {
        '@type': 'City',
        name: 'Lenexa',
        '@id': 'https://en.wikipedia.org/wiki/Lenexa,_Kansas'
      }
    ],
    openingHoursSpecification: {
      '@type': 'OpeningHoursSpecification',
      dayOfWeek: ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday'],
      opens: '08:00',
      closes: '18:00'
    },
    hasOfferCatalog: {
      '@type': 'OfferCatalog',
      name: 'Roofing & Exterior Services',
      itemListElement: [
        {
          '@type': 'Offer',
          itemOffered: {
            '@type': 'Service',
            name: 'Roof Replacement',
            description: 'Complete roof replacement with premium materials and expert installation'
          }
        },
        {
          '@type': 'Offer',
          itemOffered: {
            '@type': 'Service',
            name: 'Roof Repair',
            description: 'Fast professional roof repair services'
          }
        },
        {
          '@type': 'Offer',
          itemOffered: {
            '@type': 'Service',
            name: 'Gutter Installation',
            description: 'Seamless gutter installation and gutter guard services'
          }
        },
        {
          '@type': 'Offer',
          itemOffered: {
            '@type': 'Service',
            name: 'Siding Installation',
            description: 'Professional siding installation and repair'
          }
        },
        {
          '@type': 'Offer',
          itemOffered: {
            '@type': 'Service',
            name: 'Window Replacement',
            description: 'Energy-efficient window replacement'
          }
        },
        {
          '@type': 'Offer',
          itemOffered: {
            '@type': 'Service',
            name: 'Storm Damage Assessment',
            description: 'Full exterior storm damage inspection and insurance support'
          }
        }
      ]
    }
  }

  return (
    <script
      type="application/ld+json"
      dangerouslySetInnerHTML={{ __html: JSON.stringify(schema) }}
    />
  )
}
