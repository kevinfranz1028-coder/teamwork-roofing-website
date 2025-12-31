import Link from 'next/link'
import { FiMapPin, FiCheckCircle } from 'react-icons/fi'
import CTABand from '@/components/CTABand'

export const metadata = {
  title: 'Service Areas — Kansas City Metro | Teamwork Roofing',
  description: 'Teamwork serves the Kansas City Metro with roofing and exterior services. Roof repair, roof replacement, gutters, siding, windows, and storm inspections across KS and MO.',
}

export default function ServiceAreasPage() {
  const cities = [
    {
      name: 'Overland Park, KS',
      slug: 'overland-park-ks',
      subpages: [
        { title: 'Roof Repair', href: '/overland-park-ks/roof-repair/' },
        { title: 'Emergency Repair', href: '/overland-park-ks/emergency-roof-repair/' },
        { title: 'Roofing Contractor', href: '/overland-park-ks/roofing-contractor/' },
        { title: 'Choosing a Company', href: '/overland-park-ks/roofing-companies/' }
      ]
    },
    {
      name: 'Leawood, KS',
      slug: 'leawood-ks',
      subpages: [
        { title: 'Roof Repair', href: '/leawood-ks/roof-repair/' },
        { title: 'Emergency Repair', href: '/leawood-ks/emergency-roof-repair/' },
        { title: 'Roofing Contractor', href: '/leawood-ks/roofing-contractor/' },
        { title: 'Choosing a Company', href: '/leawood-ks/roofing-companies/' }
      ]
    },
    {
      name: 'Lenexa, KS',
      slug: 'lenexa-ks',
      subpages: [
        { title: 'Roof Repair', href: '/lenexa-ks/roof-repair/' },
        { title: 'Emergency Repair', href: '/lenexa-ks/emergency-roof-repair/' },
        { title: 'Roofing Contractor', href: '/lenexa-ks/roofing-contractor/' },
        { title: 'Choosing a Company', href: '/lenexa-ks/roofing-companies/' }
      ]
    }
  ]

  return (
    <>
      <section className="section-padding bg-light-bg">
        <div className="container-custom">
          <div className="max-w-4xl mx-auto text-center">
            <h1 className="heading-1 mb-6">
              Service Areas — <span className="text-teamwork-blue">Kansas City Metro</span>
            </h1>
            <p className="text-xl text-text-secondary mb-8">
              Teamwork serves the Kansas City Metro with roofing and exterior services — roof repair, roof replacement, gutters, siding, windows, and storm inspections.
            </p>
            <p className="text-text-secondary">
              If you don't see your city listed, call or text us at <a href="tel:9133963717" className="text-teamwork-blue hover:underline">913-396-3717</a>
            </p>
          </div>
        </div>
      </section>

      <section className="section-padding bg-white">
        <div className="container-custom">
          <h2 className="heading-2 mb-12 text-center">Featured Cities</h2>

          <div className="grid md:grid-cols-3 gap-8 max-w-6xl mx-auto">
            {cities.map((city, index) => (
              <div key={index} className="card">
                <div className="flex items-start mb-4">
                  <FiMapPin className="w-6 h-6 text-teamwork-blue mt-1 mr-3 flex-shrink-0" />
                  <div>
                    <h3 className="heading-4 mb-2">
                      <Link href={`/${city.slug}/`} className="hover:text-teamwork-blue transition-colors">
                        {city.name}
                      </Link>
                    </h3>
                  </div>
                </div>

                <ul className="space-y-2">
                  {city.subpages.map((subpage, subIndex) => (
                    <li key={subIndex}>
                      <Link
                        href={subpage.href}
                        className="text-sm text-text-secondary hover:text-teamwork-blue transition-colors flex items-start"
                      >
                        <FiCheckCircle className="w-4 h-4 text-teamwork-blue mt-0.5 mr-2 flex-shrink-0" />
                        {subpage.title}
                      </Link>
                    </li>
                  ))}
                </ul>

                <div className="mt-4 pt-4 border-t border-light-border">
                  <Link
                    href={`/${city.slug}/`}
                    className="text-sm text-teamwork-blue hover:underline font-medium"
                  >
                    View All Services in {city.name.replace(', KS', '')} →
                  </Link>
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      <section className="section-padding bg-light-bg">
        <div className="container-custom">
          <div className="max-w-3xl mx-auto text-center">
            <h2 className="heading-2 mb-6">Broader Kansas City Metro Coverage</h2>
            <p className="text-text-secondary mb-8">
              We also serve homeowners throughout Johnson County, Wyandotte County, Jackson County, and nearby areas in both Kansas and Missouri.
            </p>
            <p className="text-text-secondary">
              Cities include but are not limited to: Olathe, Shawnee, Prairie Village, Mission, Merriam, Roeland Park, Kansas City (KS & MO), Independence, Lee's Summit, and surrounding communities.
            </p>
          </div>
        </div>
      </section>

      <CTABand title="Ready to Get Started?" subtitle="Book your same-week inspection or get a quick estimate today" />
    </>
  )
}
