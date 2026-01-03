import Link from 'next/link'
import { FiShield, FiClock, FiCamera, FiDollarSign, FiCheckCircle, FiStar } from 'react-icons/fi'
import PromiseStrip from '@/components/PromiseStrip'
import CTABand from '@/components/CTABand'
import LocalProjectsSection from '@/components/LocalProjectsSection'

export const metadata = {
  title: 'Roofing Contractor Overland Park, KS | Warranty + Financing | Teamwork',
  description: 'Your Overland Park roofing contractor built on partnership. Same-week inspections, photo-proof documentation, clean site guarantee, financing, warranty.',
}

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
      description: 'We schedule and arrive fast in Overland Park - typically within 1-3 days of your call. Your time matters.'
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

  const reviews = [
    {
      name: 'Sarah M.',
      rating: 5,
      text: 'True to their name - real teamwork. Kept us informed every step, left the property spotless.'
    },
    {
      name: 'David R.',
      rating: 5,
      text: 'Professional crew, clear communication, beautiful results. Highly recommend.'
    }
  ]

  return (
    <>
      <div className="bg-white border-b border-light-border">
        <div className="container-custom py-4">
          <div className="flex items-center space-x-2 text-sm text-text-muted">
            <Link href="/" className="hover:text-teamwork-green">Home</Link>
            <span>/</span>
            <Link href="/overland-park-ks/" className="hover:text-teamwork-green">Overland Park</Link>
            <span>/</span>
            <span className="text-text-secondary">Roofing Contractor</span>
          </div>
        </div>
      </div>

      <section className="section-padding bg-light-bg">
        <div className="container-custom">
          <div className="max-w-3xl mx-auto text-center">
            <h1 className="heading-1 mb-6">
              Your Overland Park Roofing Contractor — Built on <span className="text-teamwork-green">Teamwork</span>
            </h1>
            <p className="text-xl text-text-secondary mb-8">
              More than a vendor — a partner from day one. Licensed, insured, and committed to trust, communication, and quality in every Overland Park project.
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
              Teamwork means you can trust us to treat your Overland Park home like our own - because in a partnership, your success is our success.
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
          <h2 className="heading-2 mb-12 text-center">Clean Site Guarantee Details</h2>
          <div className="max-w-3xl mx-auto">
            <div className="grid md:grid-cols-2 gap-6">
              <div className="card">
                <h4 className="font-semibold mb-3">Before We Start</h4>
                <ul className="space-y-2 text-sm text-text-secondary">
                  <li className="flex items-start"><FiCheckCircle className="w-4 h-4 text-teamwork-green mt-1 mr-2 flex-shrink-0" />Tarps for landscaping</li>
                  <li className="flex items-start"><FiCheckCircle className="w-4 h-4 text-teamwork-green mt-1 mr-2 flex-shrink-0" />Driveway protection</li>
                  <li className="flex items-start"><FiCheckCircle className="w-4 h-4 text-teamwork-green mt-1 mr-2 flex-shrink-0" />Clear site plan</li>
                </ul>
              </div>
              <div className="card">
                <h4 className="font-semibold mb-3">When We Finish</h4>
                <ul className="space-y-2 text-sm text-text-secondary">
                  <li className="flex items-start"><FiCheckCircle className="w-4 h-4 text-teamwork-green mt-1 mr-2 flex-shrink-0" />Magnetic nail sweep</li>
                  <li className="flex items-start"><FiCheckCircle className="w-4 h-4 text-teamwork-green mt-1 mr-2 flex-shrink-0" />Complete debris removal</li>
                  <li className="flex items-start"><FiCheckCircle className="w-4 h-4 text-teamwork-green mt-1 mr-2 flex-shrink-0" />Final walkthrough</li>
                </ul>
              </div>
            </div>
          </div>
        </div>
      </section>

      <LocalProjectsSection city="Overland Park" />

      <section className="section-padding bg-light-bg">
        <div className="container-custom">
          <h2 className="heading-2 mb-12 text-center">What Overland Park Customers Say</h2>
          <div className="grid md:grid-cols-2 gap-6 max-w-3xl mx-auto">
            {reviews.map((review, index) => (
              <div key={index} className="card">
                <div className="flex mb-3">
                  {[...Array(review.rating)].map((_, i) => (
                    <FiStar key={i} className="w-5 h-5 text-yellow-500 fill-current" />
                  ))}
                </div>
                <p className="text-text-secondary mb-4">{review.text}</p>
                <p className="font-semibold">{review.name}</p>
                <p className="text-sm text-text-secondary">Overland Park, KS</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      <CTABand title="Ready to Work With a Teamwork Contractor?" />
    </>
  )
}
