import Image from 'next/image'

interface Brand {
  name: string
  href: string
  logo?: string
}

interface BrandsWeInstallProps {
  variant?: 'full' | 'compact'
  title?: string
  showDisclaimer?: boolean
  brandList?: Brand[]
}

// Default brand list - use across the site for consistency
// Logo files should be placed in public/brands/ directory
export const DEFAULT_BRANDS: Brand[] = [
  {
    name: 'GAF',
    href: 'https://www.gaf.com/en-us/roofing-materials/residential-roofing-materials/shingles/timberline-hdz',
    logo: '/brands/gaf.png' // You'll need to add the actual logo file
  },
  {
    name: 'CertainTeed',
    href: 'https://www.certainteed.com/products/residential-roofing-products/landmark',
    logo: '/brands/certainteed.png'
  },
  {
    name: 'Malarkey',
    href: 'https://www.malarkeyroofing.com/products/shingles-overview/highlander-shingles/',
    logo: '/brands/malarkey.png'
  },
  {
    name: 'Owens Corning',
    href: 'https://www.owenscorning.com/en-us/roofing/duration-series-shingles',
    logo: '/brands/owens-corning.png'
  },
  {
    name: 'TAMKO',
    href: 'https://www.tamko.com/heritage',
    logo: '/brands/tamko.png'
  },
  {
    name: 'Stoneworth',
    href: 'https://stoneworthrooftile.com/',
    logo: '/brands/stoneworth.png'
  },
  {
    name: 'DaVinci',
    href: 'https://www.davinciroofscapes.com/davinci-products/',
    logo: '/brands/davinci.png'
  },
  {
    name: 'Versico',
    href: 'https://www.versico.com/en/Roofing-Products/Membranes/TPO',
    logo: '/brands/versico.png'
  },
  {
    name: 'MuleHide',
    href: 'https://www.mulehide.com/Products/p/TPOMembranes',
    logo: '/brands/mulehide.png'
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
                className="bg-white rounded-lg p-6 flex items-center justify-center hover:shadow-lg hover:scale-105 transition-all duration-300 border border-gray-200 hover:border-teamwork-blue group min-h-[120px]"
                title={`Learn more about ${brand.name}`}
              >
                {brand.logo ? (
                  <div className="relative w-full h-16 grayscale group-hover:grayscale-0 transition-all duration-300">
                    <Image
                      src={brand.logo}
                      alt={`${brand.name} logo`}
                      fill
                      className="object-contain"
                    />
                  </div>
                ) : (
                  <span className="text-lg font-bold text-gray-400 group-hover:text-teamwork-blue transition-colors">
                    {brand.name}
                  </span>
                )}
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
