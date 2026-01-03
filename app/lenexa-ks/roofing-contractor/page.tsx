import Link from 'next/link'
import { FiShield, FiClock, FiCamera, FiDollarSign, FiCheckCircle, FiStar } from 'react-icons/fi'
import PromiseStrip from '@/components/PromiseStrip'
import CTABand from '@/components/CTABand'
import LocalProjectsSection from '@/components/LocalProjectsSection'
import { cities } from '@/content/cities'

export const metadata = {
  title: 'Roofing Contractor Lenexa, KS | Warranty + Financing | Teamwork',
  description: 'Your Lenexa roofing contractor built on partnership. Same-week inspections, photo-proof documentation, clean site guarantee, financing, warranty.',
}

const cityData = cities['lenexa-ks']

export default function RoofingContractorPage() {
  const guarantees = [
    {
      icon: FiShield,
      title: 'Teamwork Warranty',
      description: 'Our installation workmanship is backed by our partnership commitment. Plus manufacturer warranties on materials from 25 years to lifetime.'
    },
    {
      icon: FiClock,
      title: 'Same-Week Inspection Promise',
      description: `We schedule and arrive fast in ${cityData.cityName} - typically within 1-3 days of your call. Your time matters.`
    },
    {
      icon: FiCheckCircle,
      title: 'Clean Site Guarantee',
      description: 'Tarps to protect landscaping, magnetic sweeps for nails, daily cleanup, final walkthrough. Your property protected.'
    },
    {
      icon: FiCamera,
      title: 'Photo-Proof Inspection',
      description: 'Every detail documented with photos. See exactly what we see. Full transparency on every project.'
    },
    {
      icon: FiDollarSign,
      title: 'Teamwork Financing Options',
      description: 'Flexible payment plans with multiple options. Make your roofing project affordable.'
    }
  ]

  const checklist = [
    'Licensed and insured in Kansas',
    'Photo documentation included with every inspection',
    'Clear written scope and timeline',
    'Clean site practices with tarps and magnetic sweeps',
    'Warranty clarity - workmanship and material coverage explained',
    'Financing options if needed',
    'References or reviews available',
    'Honest guidance on repair vs replace'
  ]

  return (
    <>
      <div className="bg-white border-b border-light-border">
        <div className="container-custom py-4">
          <div className="flex items-center space-x-2 text-sm text-text-muted">
            <Link href="/" className="hover:text-teamwork-green">Home</Link>
            <span>/</span>
            <Link href={`/${cityData.slug}/`} className="hover:text-teamwork-green">{cityData.cityName}</Link>
            <span>/</span>
            <span className="text-text-secondary">Roofing Contractor</span>
          </div>
        </div>
      </div>

      <section className="section-padding bg-light-bg">
        <div className="container-custom">
          <div className="max-w-3xl mx-auto text-center">
            <h1 className="heading-1 mb-6">
              Your {cityData.cityName} Roofing Contractor — Built on <span className="text-teamwork-green">Teamwork</span>
            </h1>
            <p className="text-xl text-text-secondary mb-8">
              More than a vendor — a partner from day one. Licensed, insured, and committed to trust, communication, and quality in every {cityData.cityName} project.
            </p>
            <div className="flex flex-col sm:flex-row gap-4 justify-center">
              <Link href="/book/" className="btn-primary">Book Same-Week Inspection</Link>
              <Link href="/estimate/" className="btn-secondary">Start Teamwork Estimate</Link>
            </div>
          </div>
        </div>
      </section>

      <PromiseStrip />

      <section className="section-padding bg-white">
        <div className="container-custom">
          <h2 className="heading-2 mb-4 text-center">Why Teamwork</h2>
          <p className="text-xl text-text-secondary text-center mb-12 max-w-3xl mx-auto">
            Every roofing contractor talks about quality. We do quality differently - with you as part of the team.
          </p>
          <div className="max-w-3xl mx-auto card">
            <p className="text-text-secondary mb-4">
              That means showing you the photos, explaining your options, respecting your property, and delivering on our promises.
            </p>
            <p className="text-text-secondary mb-4">
              It means if repair makes sense, we will repair it honestly. If replacement is smarter, we will explain why with evidence you can see.
            </p>
            <p className="text-text-secondary">
              Teamwork means you can trust us to treat your {cityData.cityName} home like our own - because in a partnership, your success is our success.
            </p>
          </div>
        </div>
      </section>

      <section className="section-padding bg-light-bg">
        <div className="container-custom">
          <h2 className="heading-2 mb-12 text-center">The 5 Guarantees</h2>
          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-8 max-w-5xl mx-auto">
            {guarantees.map((guarantee, index) => {
              const Icon = guarantee.icon
              return (
                <div key={index} className="card">
                  <Icon className="w-12 h-12 text-teamwork-green mb-4" />
                  <h4 className="font-semibold mb-2">{guarantee.title}</h4>
                  <p className="text-sm text-text-secondary">{guarantee.description}</p>
                </div>
              )
            })}
          </div>
        </div>
      </section>

      <section className="section-padding bg-white">
        <div className="container-custom">
          <h2 className="heading-2 mb-12 text-center">How to Choose a Roofing Contractor in {cityData.cityName}</h2>
          <div className="max-w-3xl mx-auto card">
            <h4 className="font-semibold mb-4">Your Contractor Selection Checklist</h4>
            <ul className="space-y-3">
              {checklist.map((item, index) => (
                <li key={index} className="flex items-start">
                  <FiCheckCircle className="w-5 h-5 text-teamwork-green mt-0.5 mr-3 flex-shrink-0" />
                  <span className="text-text-secondary">{item}</span>
                </li>
              ))}
            </ul>
          </div>
        </div>
      </section>

      <LocalProjectsSection city={cityData.cityName} />

      <section className="section-padding bg-light-bg">
        <div className="container-custom">
          <div className="max-w-3xl mx-auto text-center">
            <h2 className="heading-2 mb-6">Ready to Work Together?</h2>
            <p className="text-text-secondary mb-8">
              Book a same-week inspection in {cityData.cityName} and experience the Teamwork difference.
            </p>
            <div className="flex flex-col sm:flex-row gap-4 justify-center">
              <Link href="/book/" className="btn-primary">Book Inspection</Link>
              <a href={`tel:${cityData.phone}`} className="btn-secondary">Call {cityData.phone}</a>
            </div>
          </div>
        </div>
      </section>

      <CTABand title="Let's Start the Partnership" subtitle={`Your ${cityData.cityName} roofing project begins with trust and transparency`} />
    </>
  )
}
