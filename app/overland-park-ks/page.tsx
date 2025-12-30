import Link from 'next/link'
import { FiHome, FiTool, FiCloudRain, FiDroplet, FiLayers, FiSquare, FiCheckCircle, FiStar } from 'react-icons/fi'
import PromiseStrip from '@/components/PromiseStrip'
import CTABand from '@/components/CTABand'
import LocalProjectsSection from '@/components/LocalProjectsSection'
import NeighborhoodsSection from '@/components/NeighborhoodsSection'

export const metadata = {
  title: 'Overland Park Roofing Company | Teamwork Roofing Services',
  description: 'Teamwork Roofing Services provides roofing, gutters, siding, and windows in Overland Park, KS. Same-week inspections, photo-proof documentation, clean job sites, financing, and a Teamwork Warranty.',
}

interface FAQ {
  q: string
  a: string
  link?: {
    text: string
    href: string
  }
}

export default function OverlandParkPage() {
  const services = [
    { icon: FiTool, title: 'Roof Repair', href: '/overland-park-ks/roof-repair/' },
    { icon: FiHome, title: 'Roof Replacement', href: '/services/roof-replacement/' },
    { icon: FiCloudRain, title: 'Storm Damage', href: '/storm/' },
    { icon: FiDroplet, title: 'Gutters', href: '/services/gutters/' },
    { icon: FiLayers, title: 'Siding', href: '/services/siding/' },
    { icon: FiSquare, title: 'Windows', href: '/services/windows/' }
  ]

  const processSteps = [
    { number: 1, title: 'Same-Week Inspection', description: 'We schedule and arrive fast in Overland Park' },
    { number: 2, title: 'Photo Documentation', description: 'Every detail captured and shared with you' },
    { number: 3, title: 'Clear Options', description: 'Honest choices and pricing — no pressure' },
    { number: 4, title: 'Expert Installation', description: 'Professional work with clean site practices' },
    { number: 5, title: 'Teamwork Warranty', description: 'Backed by our partnership commitment' }
  ]

  const neighborhoods = [
    'Downtown Overland Park',
    'Old Overland Park',
    'Nottingham by the Green',
    'Nall Hills',
    'Stanley',
    'Cherokee Hills',
    'Maple Crest',
    'Wilshire by the Lake',
    'Deer Creek',
    'LionsGate',
    'Red Fox',
    'Indian Creek'
  ]

  const reviews = [
    {
      name: 'Sarah M.',
      city: 'Overland Park',
      rating: 5,
      text: 'True to their name — real teamwork. They kept us informed every step, left the property spotless, and the roof looks incredible.'
    },
    {
      name: 'David R.',
      city: 'Overland Park',
      rating: 5,
      text: 'Same-week inspection promise delivered! Professional crew, clear communication, and beautiful results.'
    },
    {
      name: 'Jennifer K.',
      city: 'Overland Park',
      rating: 5,
      text: 'The photo documentation was so helpful. Clean site guarantee is real - you would never know they were here except for the beautiful new roof.'
    }
  ]

  const faqs: FAQ[] = [
    {
      q: 'Do you serve all of Overland Park?',
      a: 'Yes — we serve homeowners across all of Overland Park, including Downtown and Old Overland Park, Nall Hills, Stanley, Deer Creek, Wilshire by the Lake, and surrounding neighborhoods.'
    },
    {
      q: 'How fast can you inspect my roof in Overland Park?',
      a: 'We promise same-week inspections. Most Overland Park inspections are scheduled within 1-3 days of your call.'
    },
    {
      q: 'Do you provide photo documentation?',
      a: 'Yes, every inspection includes detailed photos so you can see exactly what we see. Full transparency.'
    },
    {
      q: 'Can you inspect my roof after hail or wind storms in Overland Park?',
      a: 'Yes. We offer same-week storm inspections with professional photo documentation and a clear scope of recommended repairs. Book a storm inspection and we'll walk you through what we see.',
      link: { text: 'storm inspections', href: '/storm/' }
    },
    {
      q: 'Do you offer emergency roof leak help in Overland Park?',
      a: 'Yes. If you have an active leak, call or text us right now. We will help you take the next best step and schedule an urgent inspection.',
      link: { text: 'emergency roof leak help', href: '/overland-park-ks/emergency-roof-repair/' }
    },
    {
      q: 'Are you licensed and insured in Kansas?',
      a: 'Yes, we are fully licensed and insured to work throughout Kansas including Overland Park and Johnson County.'
    },
    {
      q: 'Do you offer financing?',
      a: 'Yes, we offer Teamwork Financing options with flexible terms to fit your budget.'
    },
    {
      q: 'What is your warranty?',
      a: 'Our Teamwork Warranty covers installation workmanship, plus manufacturer warranties on materials (25 years to lifetime depending on product).'
    }
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
            name: 'Teamwork Roofing Services - Overland Park',
            image: 'https://teamworkroofing.com/logo.png',
            '@id': 'https://teamworkroofing.com/overland-park-ks/',
            url: 'https://teamworkroofing.com/overland-park-ks/',
            telephone: '+1-913-396-3717',
            address: {
              '@type': 'PostalAddress',
              addressLocality: 'Overland Park',
              addressRegion: 'KS',
              addressCountry: 'US'
            },
            geo: {
              '@type': 'GeoCoordinates',
              latitude: 38.9822,
              longitude: -94.6708
            },
            areaServed: {
              '@type': 'City',
              name: 'Overland Park'
            },
            priceRange: '$$'
          })
        }}
      />

      {/* Hero */}
      <section className="section-padding bg-dark-bg">
        <div className="container-custom">
          <div className="max-w-4xl mx-auto text-center">
            <h1 className="heading-1 mb-6">
              Roofing & Exteriors in <span className="text-teamwork-blue">Overland Park, KS</span> — Done The Teamwork Way
            </h1>
            <p className="text-xl text-gray-400 mb-8">
              A partnership from day one. Teamwork is a local roofing company in Overland Park, KS providing roof repair, roof replacement, and storm inspections—backed by photo-proof documentation, clean site practices, flexible financing, and a Teamwork Warranty.
            </p>

            <div className="flex flex-col sm:flex-row gap-4 justify-center mb-6">
              <Link href="/book/" className="btn-primary">
                Book Same-Week Inspection
              </Link>
              <Link href="/estimate/" className="btn-secondary">
                Start Teamwork Estimate
              </Link>
            </div>

            <p className="text-sm text-gray-400 mb-6 text-center">
              Looking for a roofer in Overland Park? Start with a same-week inspection.
            </p>

            <div className="flex flex-wrap items-center justify-center gap-3 mb-6">
              <span className="px-3 py-1 bg-dark-surface border border-dark-border rounded-full text-xs text-gray-400">Licensed & Insured</span>
              <span className="px-3 py-1 bg-dark-surface border border-dark-border rounded-full text-xs text-gray-400">Photo-Proof Inspection</span>
              <span className="px-3 py-1 bg-dark-surface border border-dark-border rounded-full text-xs text-gray-400">Clean Site Guarantee</span>
              <span className="px-3 py-1 bg-dark-surface border border-dark-border rounded-full text-xs text-gray-400">Same-Week Inspections</span>
              <span className="px-3 py-1 bg-dark-surface border border-dark-border rounded-full text-xs text-gray-400">Financing Options</span>
            </div>

            <div className="flex items-center justify-center gap-6 text-gray-400">
              <a href="tel:9133963717" className="hover:text-teamwork-blue transition-colors">
                <FiCheckCircle className="inline w-5 h-5 mr-2" />
                Call: 913-396-3717
              </a>
              <a href="sms:9133963717" className="hover:text-teamwork-blue transition-colors">
                Text: 913-396-3717
              </a>
            </div>
          </div>
        </div>
      </section>

      {/* Service Tiles */}
      <section className="section-padding bg-dark-surface">
        <div className="container-custom">
          <h2 className="heading-2 mb-4 text-center">Our Services in Overland Park</h2>
          <p className="text-gray-400 text-center mb-12 max-w-3xl mx-auto">
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

      <LocalProjectsSection city="Overland Park" />

      {/* The Teamwork Process */}
      <section className="section-padding bg-dark-bg">
        <div className="container-custom">
          <h2 className="heading-2 mb-4 text-center">The Teamwork Process</h2>
          <p className="text-xl text-gray-400 text-center mb-12">Five steps, five promises</p>

          <div className="grid md:grid-cols-5 gap-6">
            {processSteps.map((step, index) => (
              <div key={index} className="text-center">
                <div className="w-16 h-16 rounded-full bg-teamwork-blue/10 border-2 border-teamwork-blue flex items-center justify-center mx-auto mb-4">
                  <span className="text-2xl font-bold text-teamwork-blue">{step.number}</span>
                </div>
                <h4 className="font-semibold mb-2">{step.title}</h4>
                <p className="text-sm text-gray-400">{step.description}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      <NeighborhoodsSection city="Overland Park" neighborhoods={neighborhoods} />

      {/* Metro Coverage Link */}
      <section className="py-6 bg-dark-bg">
        <div className="container-custom">
          <p className="text-sm text-gray-400 text-center">
            <Link href="/" className="hover:text-teamwork-blue hover:underline transition-colors">
              Serving more than Overland Park? View Kansas City Metro coverage →
            </Link>
          </p>
        </div>
      </section>

      {/* Reviews */}
      <section className="section-padding bg-dark-surface">
        <div className="container-custom">
          <h2 className="heading-2 mb-12 text-center">What Overland Park Customers Say</h2>

          <div className="grid md:grid-cols-3 gap-6 mb-8">
            {reviews.map((review, index) => (
              <div key={index} className="card">
                <div className="flex mb-3">
                  {[...Array(review.rating)].map((_, i) => (
                    <FiStar key={i} className="w-5 h-5 text-yellow-500 fill-current" />
                  ))}
                </div>
                <p className="text-gray-300 mb-4">{review.text}</p>
                <div className="border-t border-dark-border pt-4">
                  <p className="font-semibold">{review.name}</p>
                  <p className="text-sm text-gray-400">{review.city}, KS</p>
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
      <section className="section-padding bg-dark-bg">
        <div className="container-custom">
          <h2 className="heading-2 mb-12 text-center">Overland Park Roofing FAQ</h2>

          <div className="max-w-3xl mx-auto space-y-4">
            {faqs.map((faq, index) => (
              <div key={index} className="card">
                <h4 className="font-semibold mb-2">{faq.q}</h4>
                <p className="text-gray-400 text-sm">
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

      <CTABand title="Ready to Get Started in Overland Park?" subtitle="Book your same-week inspection or get a quick estimate today" />
    </>
  )
}
