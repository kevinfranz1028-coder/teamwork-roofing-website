import Link from 'next/link'
import { FiHome, FiTool, FiCloudRain, FiDroplet, FiLayers, FiSquare, FiCheckCircle, FiStar } from 'react-icons/fi'
import PromiseStrip from '@/components/PromiseStrip'
import CTABand from '@/components/CTABand'
import LocalProjectsSection from '@/components/LocalProjectsSection'
import NeighborhoodsSection from '@/components/NeighborhoodsSection'
import { cities } from '@/content/cities'

export const metadata = {
  title: 'Leawood Roofing Company | Teamwork Roofing Services',
  description: 'Teamwork Roofing Services provides roofing, gutters, siding, and windows in Leawood, KS. Same-week inspections, photo-proof documentation, clean job sites, financing, and a Teamwork Warranty.',
}

const cityData = cities['leawood-ks']

export default function LeawoodPage() {
  const services = [
    { icon: FiTool, title: 'Roof Repair', href: '/leawood-ks/roof-repair/' },
    { icon: FiHome, title: 'Roof Replacement', href: '/leawood-ks/roof-replacement/' },
    { icon: FiCloudRain, title: 'Storm Damage', href: '/storm/' },
    { icon: FiDroplet, title: 'Gutters', href: '/services/gutters/' },
    { icon: FiLayers, title: 'Siding', href: '/services/siding/' },
    { icon: FiSquare, title: 'Windows', href: '/services/windows/' }
  ]

  const processSteps = [
    { number: 1, title: 'Same-Week Inspection', description: `We schedule and arrive fast in ${cityData.cityName}` },
    { number: 2, title: 'Photo Documentation', description: 'Every detail captured and shared with you' },
    { number: 3, title: 'Clear Options', description: 'Honest choices and pricing — no pressure' },
    { number: 4, title: 'Expert Installation', description: 'Professional work with clean site practices' },
    { number: 5, title: 'Teamwork Warranty', description: 'Backed by our partnership commitment' }
  ]

  return (
    <>
      {/* Schema Markup */}
      <script
        type="application/ld+json"
        dangerouslySetInnerHTML={{
          __html: JSON.stringify({
            '@context': 'https://schema.org',
            '@type': 'LocalBusiness',
            name: `Teamwork Roofing Services - ${cityData.cityName}`,
            image: 'https://teamworkroofing.com/logo.png',
            '@id': `https://teamworkroofing.com/${cityData.slug}/`,
            url: `https://teamworkroofing.com/${cityData.slug}/`,
            telephone: `+1-${cityData.phone.replace(/-/g, '')}`,
            address: {
              '@type': 'PostalAddress',
              addressLocality: cityData.cityName,
              addressRegion: cityData.state,
              addressCountry: 'US'
            },
            areaServed: {
              '@type': 'City',
              name: cityData.cityName
            },
            priceRange: '$$'
          })
        }}
      />

      {/* Hero */}
      <section className="section-padding bg-light-bg">
        <div className="container-custom">
          <div className="max-w-4xl mx-auto text-center">
            <h1 className="heading-1 mb-6">
              Roofing & Exteriors in <span className="text-teamwork-blue">{cityData.cityName}, {cityData.state}</span> — Done The Teamwork Way
            </h1>
            <p className="text-xl text-text-secondary mb-8">
              {cityData.hub.intro}
            </p>

            <div className="flex flex-col sm:flex-row gap-4 justify-center mb-6">
              <Link href="/book/" className="btn-primary">
                Book Same-Week Inspection
              </Link>
              <Link href="/estimate/" className="btn-secondary">
                Start Teamwork Estimate
              </Link>
            </div>

            <p className="text-sm text-text-secondary mb-6 text-center">
              Looking for a roofer in {cityData.cityName}? Start with a same-week inspection.
            </p>

            <div className="flex flex-wrap items-center justify-center gap-3 mb-6">
              <span className="px-3 py-1 bg-white border border-light-border rounded-full text-xs text-text-secondary">Licensed & Insured</span>
              <span className="px-3 py-1 bg-white border border-light-border rounded-full text-xs text-text-secondary">Photo-Proof Inspection</span>
              <span className="px-3 py-1 bg-white border border-light-border rounded-full text-xs text-text-secondary">Clean Site Guarantee</span>
              <span className="px-3 py-1 bg-white border border-light-border rounded-full text-xs text-text-secondary">Same-Week Inspections</span>
              <span className="px-3 py-1 bg-white border border-light-border rounded-full text-xs text-text-secondary">Financing Options</span>
            </div>

            <div className="flex items-center justify-center gap-6 text-text-secondary">
              <a href={`tel:${cityData.phone}`} className="hover:text-teamwork-blue transition-colors">
                <FiCheckCircle className="inline w-5 h-5 mr-2" />
                Call: {cityData.phone}
              </a>
              <a href={`sms:${cityData.phone}`} className="hover:text-teamwork-blue transition-colors">
                Text: {cityData.phone}
              </a>
            </div>
          </div>
        </div>
      </section>

      {/* Service Tiles */}
      <section className="section-padding bg-white">
        <div className="container-custom">
          <h2 className="heading-2 mb-4 text-center">Our Services in {cityData.cityName}</h2>
          <p className="text-text-secondary text-center mb-12 max-w-3xl mx-auto">
            Roof repair, roof replacement, and exterior upgrades—done with clear communication, clean job sites, and photo documentation.
          </p>
          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
            {services.map((service, index) => {
              const Icon = service.icon
              return (
                <Link
                  key={index}
                  href={service.href}
                  className="card hover:border-teamwork-blue transition-all duration-200 group"
                >
                  <Icon className="w-12 h-12 text-teamwork-blue mb-4 group-hover:scale-110 transition-transform" />
                  <h3 className="text-xl font-semibold">{service.title}</h3>
                </Link>
              )
            })}
          </div>
        </div>
      </section>

      <PromiseStrip />

      <LocalProjectsSection city={cityData.cityName} />

      {/* The Teamwork Process */}
      <section className="section-padding bg-light-bg">
        <div className="container-custom">
          <h2 className="heading-2 mb-4 text-center">The Teamwork Process</h2>
          <p className="text-xl text-text-secondary text-center mb-12">Five steps, five promises</p>

          <div className="grid md:grid-cols-5 gap-6">
            {processSteps.map((step, index) => (
              <div key={index} className="text-center">
                <div className="w-16 h-16 rounded-full bg-teamwork-blue/10 border-2 border-teamwork-blue flex items-center justify-center mx-auto mb-4">
                  <span className="text-2xl font-bold text-teamwork-blue">{step.number}</span>
                </div>
                <h4 className="font-semibold mb-2">{step.title}</h4>
                <p className="text-sm text-text-secondary">{step.description}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      <NeighborhoodsSection city={cityData.cityName} neighborhoods={cityData.neighborhoods} />

      {/* Local Proof */}
      <section className="py-12 bg-white">
        <div className="container-custom">
          <div className="max-w-3xl mx-auto">
            <h3 className="heading-3 mb-6 text-center">{cityData.localProof.title}</h3>
            <ul className="space-y-3 mb-4">
              {cityData.localProof.bullets.map((bullet, index) => (
                <li key={index} className="flex items-start">
                  <FiCheckCircle className="w-5 h-5 text-teamwork-blue mt-1 mr-3 flex-shrink-0" />
                  <span className="text-text-secondary">{bullet}</span>
                </li>
              ))}
            </ul>
            <p className="text-xs text-text-muted text-center">{cityData.localProof.disclaimer}</p>
          </div>
        </div>
      </section>

      {/* Metro Coverage Link */}
      <section className="py-6 bg-light-bg">
        <div className="container-custom">
          <p className="text-sm text-text-secondary text-center">
            <Link href="/service-areas/" className="hover:text-teamwork-blue hover:underline transition-colors">
              Serving more than {cityData.cityName}? View Kansas City Metro coverage →
            </Link>
          </p>
        </div>
      </section>

      {/* Reviews */}
      <section className="section-padding bg-white">
        <div className="container-custom">
          <h2 className="heading-2 mb-12 text-center">What {cityData.cityName} Customers Say</h2>

          <div className="grid md:grid-cols-3 gap-6 mb-8">
            {cityData.reviews.map((review, index) => (
              <div key={index} className="card">
                <div className="flex mb-3">
                  {[...Array(review.rating)].map((_, i) => (
                    <FiStar key={i} className="w-5 h-5 text-yellow-500 fill-current" />
                  ))}
                </div>
                <p className="text-text-secondary mb-4">{review.text}</p>
                <div className="border-t border-light-border pt-4">
                  <p className="font-semibold">{review.name}</p>
                  <p className="text-sm text-text-secondary">{review.city}, {cityData.state}</p>
                </div>
              </div>
            ))}
          </div>

          <div className="text-center">
            <Link href="/reviews/" className="btn-secondary">
              Read All Reviews
            </Link>
          </div>
        </div>
      </section>

      {/* FAQ */}
      <section className="section-padding bg-light-bg">
        <div className="container-custom">
          <h2 className="heading-2 mb-12 text-center">{cityData.cityName} Roofing FAQ</h2>

          <div className="max-w-3xl mx-auto space-y-4">
            {cityData.faqs.map((faq, index) => (
              <div key={index} className="card">
                <h4 className="font-semibold mb-2">{faq.q}</h4>
                <p className="text-text-secondary text-sm">
                  {faq.link ? (
                    <>
                      {faq.a.split(faq.link.text)[0]}
                      <Link href={faq.link.href} className="text-teamwork-blue hover:underline">
                        {faq.link.text}
                      </Link>
                      {faq.a.split(faq.link.text)[1]}
                    </>
                  ) : (
                    faq.a
                  )}
                </p>
              </div>
            ))}
          </div>

          <div className="text-center mt-8">
            <Link href="/faq/" className="text-teamwork-blue hover:underline">
              View All FAQs →
            </Link>
          </div>
        </div>
      </section>

      <CTABand title={`Ready to Get Started in ${cityData.cityName}?`} subtitle="Book your same-week inspection or get a quick estimate today" />
    </>
  )
}
