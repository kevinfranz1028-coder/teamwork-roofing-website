interface Brand {
  name: string
  href: string
}

interface BrandsWeInstallProps {
  variant?: 'full' | 'compact'
  title?: string
  showDisclaimer?: boolean
  brandList?: Brand[]
}

// Default brand list - use across the site for consistency
export const DEFAULT_BRANDS: Brand[] = [
  { name: 'GAF', href: 'https://www.gaf.com/en-us/roofing-materials/residential-roofing-materials/shingles/timberline-hdz' },
  { name: 'CertainTeed', href: 'https://www.certainteed.com/products/residential-roofing-products/landmark' },
  { name: 'Malarkey', href: 'https://www.malarkeyroofing.com/products/shingles-overview/highlander-shingles/' },
  { name: 'Owens Corning', href: 'https://www.owenscorning.com/en-us/roofing/duration-series-shingles' },
  { name: 'TAMKO', href: 'https://www.tamko.com/heritage' },
  { name: 'Stoneworth', href: 'https://stoneworthrooftile.com/' },
  { name: 'DaVinci', href: 'https://www.davinciroofscapes.com/davinci-products/' },
  { name: 'Versico', href: 'https://www.versico.com/en/Roofing-Products/Membranes/TPO' },
  { name: 'MuleHide', href: 'https://www.mulehide.com/Products/p/TPOMembranes' }
]

export default function BrandsWeInstall({
  variant = 'full',
  title = 'Brands We Install',
  showDisclaimer = true,
  brandList = DEFAULT_BRANDS
}: BrandsWeInstallProps) {
  return (
    <section className={`${variant === 'full' ? 'section-padding' : 'py-12'} bg-white`}>
      <div className="container-custom">
        <div className="max-w-4xl mx-auto text-center">
          <h2 className={variant === 'full' ? 'heading-2 mb-4' : 'heading-3 mb-4'}>
            {title}
          </h2>
          <p className="text-text-secondary mb-8">
            We install manufacturer-grade systems based on your home, budget, and storm conditions.
          </p>

          <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4 mb-6">
            {brandList.map((brand, index) => (
              <a
                key={index}
                href={brand.href}
                target="_blank"
                rel="noopener noreferrer"
                className="card text-center hover:border-teamwork-blue transition-all duration-200 group"
              >
                <span className="text-lg font-semibold group-hover:text-teamwork-blue transition-colors">
                  {brand.name}
                </span>
              </a>
            ))}
          </div>

          {showDisclaimer && (
            <p className="text-xs text-text-muted mt-8">
              Brand names and trademarks are the property of their respective owners. Teamwork Roofing Services LLC is an independent contractor and is not affiliated with or endorsed by these manufacturers.
            </p>
          )}
        </div>
      </div>
    </section>
  )
}
