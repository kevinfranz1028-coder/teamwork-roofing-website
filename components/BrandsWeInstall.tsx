import Image from 'next/image'

interface Brand {
  name: string
  href: string
  logo?: string
  color?: string // Brand color for styling
}

interface BrandsWeInstallProps {
  variant?: 'full' | 'compact'
  title?: string
  showDisclaimer?: boolean
  brandList?: Brand[]
}

// Default brand list - use across the site for consistency
// Residential roofing brands only
export const DEFAULT_BRANDS: Brand[] = [
  {
    name: 'GAF',
    href: 'https://www.gaf.com/en-us/roofing-materials/residential-roofing-materials/shingles/timberline-hdz',
    color: '#E31837'
  },
  {
    name: 'CertainTeed',
    href: 'https://www.certainteed.com/products/residential-roofing-products/landmark',
    color: '#003DA5'
  },
  {
    name: 'Malarkey',
    href: 'https://www.malarkeyroofing.com/products/shingles-overview/highlander-shingles/',
    color: '#C41E3A'
  },
  {
    name: 'Owens Corning',
    href: 'https://www.owenscorning.com/en-us/roofing/duration-series-shingles',
    color: '#E4007C'
  },
  {
    name: 'TAMKO',
    href: 'https://www.tamko.com/heritage',
    color: '#003B5C'
  },
  {
    name: 'IKO',
    href: 'https://www.iko.com/na/products/residential-roofing/',
    color: '#005EB8'
  }
]

export default function BrandsWeInstall({
  variant = 'full',
  title = 'Brands We Install',
  showDisclaimer = true,
  brandList = DEFAULT_BRANDS
}: BrandsWeInstallProps) {
  return (
    <section className={`${variant === 'full' ? 'section-padding' : 'py-12'} bg-gray-50`}>
      <div className="container-custom">
        <div className="max-w-6xl mx-auto">
          <div className="text-center mb-12">
            <h2 className={variant === 'full' ? 'heading-2 mb-4' : 'heading-3 mb-4'}>
              {title}
            </h2>
            <p className="text-text-secondary max-w-2xl mx-auto">
              We install manufacturer-grade systems based on your home, budget, and storm conditions.
            </p>
          </div>

          <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-5 gap-6">
            {brandList.map((brand, index) => (
              <a
                key={index}
                href={brand.href}
                target="_blank"
                rel="noopener noreferrer"
                className="group bg-white rounded-lg p-6 flex items-center justify-center hover:shadow-lg hover:scale-105 transition-all duration-300 border border-gray-200 hover:border-teamwork-blue min-h-[120px] relative overflow-hidden"
                title={`Learn more about ${brand.name}`}
              >
                {/* Subtle background accent on hover */}
                <div
                  className="absolute inset-0 opacity-0 group-hover:opacity-5 transition-opacity duration-300"
                  style={{ backgroundColor: brand.color || '#00AEEF' }}
                ></div>

                {/* Brand name styled as logo */}
                <div className="relative z-10 text-center">
                  <span
                    className="text-xl font-black tracking-tight text-gray-400 group-hover:text-gray-800 transition-colors duration-300"
                    style={{
                      fontFamily: 'system-ui, -apple-system, sans-serif',
                      textTransform: 'uppercase',
                      letterSpacing: brand.name.length > 8 ? '-0.02em' : '0.05em'
                    }}
                  >
                    {brand.name}
                  </span>

                  {/* Underline accent */}
                  <div
                    className="h-0.5 w-0 group-hover:w-full transition-all duration-300 mx-auto mt-1.5"
                    style={{ backgroundColor: brand.color || '#00AEEF' }}
                  ></div>
                </div>
              </a>
            ))}
          </div>

          {showDisclaimer && (
            <p className="text-xs text-text-muted mt-10 text-center max-w-3xl mx-auto">
              Brand names and trademarks are the property of their respective owners. Teamwork Roofing Services LLC is an independent contractor and is not affiliated with or endorsed by these manufacturers.
            </p>
          )}
        </div>
      </div>
    </section>
  )
}
