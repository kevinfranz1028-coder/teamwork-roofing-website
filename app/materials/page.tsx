import Link from 'next/link'
import CTABand from '@/components/CTABand'

export const metadata = {
  title: 'Roofing Materials & Systems We Install | Teamwork Roofing',
  description: 'Teamwork Roofing installs premium roofing systems including architectural shingles, synthetic slate, concrete tile, and low-slope membranes from leading manufacturers.',
}

interface Brand {
  name: string
  href: string
}

const architecturalShingleBrands: Brand[] = [
  { name: 'GAF', href: 'https://www.gaf.com/en-us/roofing-materials/residential-roofing-materials/shingles/timberline-hdz' },
  { name: 'CertainTeed', href: 'https://www.certainteed.com/products/residential-roofing-products/landmark' },
  { name: 'Malarkey', href: 'https://www.malarkeyroofing.com/products/shingles-overview/highlander-shingles/' },
  { name: 'Owens Corning', href: 'https://www.owenscorning.com/en-us/roofing/duration-series-shingles' },
  { name: 'TAMKO', href: 'https://www.tamko.com/heritage' }
]

const syntheticBrands: Brand[] = [
  { name: 'DaVinci', href: 'https://www.davinciroofscapes.com/davinci-products/' }
]

const concreteTileBrands: Brand[] = [
  { name: 'Stoneworth', href: 'https://stoneworthrooftile.com/' }
]

const lowSlopeBrands: Brand[] = [
  { name: 'Versico', href: 'https://www.versico.com/en/Roofing-Products/Membranes/TPO' },
  { name: 'MuleHide', href: 'https://www.mulehide.com/Products/p/TPOMembranes' }
]

function BrandChips({ brands }: { brands: Brand[] }) {
  return (
    <div className="flex flex-wrap gap-3 justify-center">
      {brands.map((brand, index) => (
        <a
          key={index}
          href={brand.href}
          target="_blank"
          rel="noopener noreferrer"
          className="px-4 py-2 bg-dark-bg border border-dark-border rounded-full text-sm font-semibold hover:border-teamwork-blue hover:text-teamwork-blue transition-all duration-200"
        >
          {brand.name}
        </a>
      ))}
    </div>
  )
}

export default function MaterialsPage() {
  return (
    <>
      {/* Hero */}
      <section className="section-padding bg-dark-bg">
        <div className="container-custom">
          <div className="max-w-4xl mx-auto text-center">
            <h1 className="heading-1 mb-6">
              Roofing Materials & Systems <span className="text-teamwork-blue">We Install</span>
            </h1>
            <p className="text-xl text-gray-400 mb-8">
              We help you choose the right roofing system for your home, budget, and Kansas City weather conditions. Every installation follows manufacturer specifications and includes photo documentation, clean site practices, and our Teamwork Warranty.
            </p>
            <div className="flex flex-col sm:flex-row gap-4 justify-center">
              <Link href="/book/" className="btn-primary">
                Book Same-Week Inspection
              </Link>
              <Link href="/estimate/" className="btn-secondary">
                Start Teamwork Estimate
              </Link>
            </div>
          </div>
        </div>
      </section>

      {/* Architectural Asphalt Shingles */}
      <section className="section-padding bg-dark-surface">
        <div className="container-custom">
          <div className="max-w-4xl mx-auto">
            <h2 className="heading-2 mb-4 text-center">Architectural Asphalt Shingles</h2>
            <p className="text-gray-400 text-center mb-8">
              The most popular roofing choice for Kansas City homes. Architectural shingles offer excellent wind and hail resistance, dimensional appearance, and manufacturer warranties ranging from 25 years to lifetime.
            </p>
            <BrandChips brands={architecturalShingleBrands} />
          </div>
        </div>
      </section>

      {/* Synthetic Slate/Shake */}
      <section className="section-padding bg-dark-bg">
        <div className="container-custom">
          <div className="max-w-4xl mx-auto">
            <h2 className="heading-2 mb-4 text-center">Synthetic Slate & Shake</h2>
            <p className="text-gray-400 text-center mb-8">
              Premium appearance with advanced polymer engineering. Lighter than natural slate, impact-resistant, and designed for long-term performance with exceptional curb appeal.
            </p>
            <BrandChips brands={syntheticBrands} />
          </div>
        </div>
      </section>

      {/* Concrete Tile */}
      <section className="section-padding bg-dark-surface">
        <div className="container-custom">
          <div className="max-w-4xl mx-auto">
            <h2 className="heading-2 mb-4 text-center">Concrete Tile</h2>
            <p className="text-gray-400 text-center mb-8">
              Durable, fire-resistant, and available in a variety of profiles and colors. Concrete tile roofing provides superior longevity and distinctive architectural style.
            </p>
            <BrandChips brands={concreteTileBrands} />
          </div>
        </div>
      </section>

      {/* Low-Slope Membranes */}
      <section className="section-padding bg-dark-bg">
        <div className="container-custom">
          <div className="max-w-4xl mx-auto">
            <h2 className="heading-2 mb-4 text-center">Low-Slope Membranes</h2>
            <p className="text-gray-400 text-center mb-8">
              Single-ply TPO and EPDM membranes for flat or low-slope residential and commercial applications. Energy-efficient, weather-resistant, and designed for proper drainage and long-term performance.
            </p>
            <BrandChips brands={lowSlopeBrands} />
          </div>
        </div>
      </section>

      {/* How We Help You Choose */}
      <section className="section-padding bg-dark-surface">
        <div className="container-custom">
          <div className="max-w-4xl mx-auto">
            <h2 className="heading-2 mb-12 text-center">How We Help You Choose</h2>
            <div className="grid md:grid-cols-2 gap-8">
              <div className="card">
                <h3 className="text-xl font-semibold mb-3">Photo Documentation</h3>
                <p className="text-gray-400 text-sm">
                  We show you the current condition of your roof with clear photos so you understand what needs attention and why.
                </p>
              </div>
              <div className="card">
                <h3 className="text-xl font-semibold mb-3">Clear Options</h3>
                <p className="text-gray-400 text-sm">
                  We explain the differences between systems, warranties, and price points — no pressure, just honest guidance.
                </p>
              </div>
              <div className="card">
                <h3 className="text-xl font-semibold mb-3">Code & Ventilation</h3>
                <p className="text-gray-400 text-sm">
                  We review local code requirements and proper ventilation to ensure your roof performs as designed.
                </p>
              </div>
              <div className="card">
                <h3 className="text-xl font-semibold mb-3">Manufacturer Specs</h3>
                <p className="text-gray-400 text-sm">
                  Every installation follows manufacturer specifications to protect your warranty and your investment.
                </p>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Disclaimer */}
      <section className="py-8 bg-dark-bg">
        <div className="container-custom">
          <p className="text-xs text-gray-500 text-center max-w-4xl mx-auto">
            Brand names and trademarks are the property of their respective owners. Teamwork Roofing Services LLC is an independent contractor and is not affiliated with or endorsed by these manufacturers.
          </p>
        </div>
      </section>

      <CTABand
        title="Ready to Choose Your Roofing System?"
        subtitle="Book a same-week inspection and we'll walk you through your options with photo documentation"
      />
    </>
  )
}
