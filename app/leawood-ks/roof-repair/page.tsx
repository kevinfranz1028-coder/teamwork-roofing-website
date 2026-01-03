import Link from 'next/link'
import { FiCheckCircle, FiPhone, FiMessageSquare, FiShield } from 'react-icons/fi'
import PromiseStrip from '@/components/PromiseStrip'
import CTABand from '@/components/CTABand'
import LocalProjectsSection from '@/components/LocalProjectsSection'
import NeighborhoodsSection from '@/components/NeighborhoodsSection'
import { cities } from '@/content/cities'

export const metadata = {
  title: 'Roof Repair Leawood, KS | Same-Week Inspections | Teamwork',
  description: 'Fast, professional roof repair in Leawood. Same-week inspections, photo-proof documentation, honest repair vs replace guidance. Call 913-396-3717',
}

const cityData = cities['leawood-ks']

export default function LeawoodRoofRepairPage() {
  const commonProblems = [
    { title: 'Missing or damaged shingles', description: 'Wind, age, or impact damage causing exposed areas' },
    { title: 'Flashing failures', description: 'Gaps around chimneys, vents, or valleys allowing water intrusion' },
    { title: 'Vent boot cracks', description: 'Deteriorated rubber boots around pipe penetrations' },
    { title: 'Storm damage', description: 'Hail impacts, wind tears, or debris damage from recent weather' },
    { title: 'Active leaks', description: 'Water stains on ceilings, wet insulation, or visible drips' },
    { title: 'Granule loss', description: 'Excessive shingle wear exposing the mat underneath' }
  ]

  const timeline = [
    'Call or text us — we respond same day',
    'Schedule same-week inspection at your convenience',
    'Full roof inspection with photo documentation',
    'Honest repair vs replace assessment',
    'Clear pricing and timeline',
    'Professional repair with clean site practices',
    'Warranty activation'
  ]

  const faqs = [
    {
      q: `How fast can you repair my roof in ${cityData.cityName}?`,
      a: 'Most repairs are completed within 3-5 business days of inspection. Emergency leaks can often be temporarily mitigated same-day or next-day.'
    },
    {
      q: 'Should I repair or replace my roof?',
      a: 'We will show you photos and give you honest guidance. If your roof has years of life left and the damage is isolated, repair makes sense. If it is near the end of its lifespan or damage is widespread, we will explain why replacement is smarter long-term.'
    },
    {
      q: 'Do you provide photo documentation for repairs?',
      a: 'Yes, every inspection includes photos of the damage before and after repair so you have complete documentation.'
    },
    {
      q: 'Is roof repair covered by your warranty?',
      a: 'Yes, our repair work is backed by our Teamwork Warranty on workmanship.'
    },
    {
      q: 'Can you help with insurance claims for storm damage?',
      a: 'We provide detailed photo documentation and repair estimates you can share with your insurer. We are not public adjusters and do not negotiate claims.'
    },
    {
      q: 'What if the damage is worse than expected?',
      a: 'If we discover additional issues during repair, we will document them with photos, explain your options, and get your approval before proceeding.'
    }
  ]

  return (
    <>
      {/* Breadcrumbs */}
      <div className="bg-white border-b border-light-border">
        <div className="container-custom py-4">
          <div className="flex items-center space-x-2 text-sm text-text-muted">
            <Link href="/" className="hover:text-teamwork-blue">Home</Link>
            <span>/</span>
            <Link href={`/${cityData.slug}/`} className="hover:text-teamwork-blue">{cityData.cityName}</Link>
            <span>/</span>
            <span className="text-text-secondary">Roof Repair</span>
          </div>
        </div>
      </div>

      {/* Hero */}
      <section className="section-padding bg-light-bg">
        <div className="container-custom">
          <div className="max-w-3xl">
            <h1 className="heading-1 mb-6">
              Roof Repair in <span className="text-teamwork-blue">{cityData.cityName}, {cityData.state}</span>
            </h1>
            <p className="text-xl text-text-secondary mb-8">
              Fast, professional roof repair with photo-proof documentation, honest guidance, and clean site practices. Serving all {cityData.cityName} neighborhoods with same-week inspections.
            </p>

            <div className="flex flex-wrap gap-4 mb-6">
              <a href={`tel:${cityData.phone}`} className="btn-primary">
                <FiPhone className="inline mr-2" />
                Call {cityData.phone}
              </a>
              <a href={`sms:${cityData.phone}`} className="btn-secondary">
                <FiMessageSquare className="inline mr-2" />
                Text Us
              </a>
              <Link href="/book/" className="btn-secondary">
                Book Inspection
              </Link>
            </div>

            <div className="flex items-start space-x-2 text-sm text-text-muted">
              <FiShield className="w-5 h-5 text-teamwork-blue mt-0.5 flex-shrink-0" />
              <span>All repairs backed by Teamwork Warranty</span>
            </div>
          </div>
        </div>
      </section>

      <PromiseStrip />

      {/* Common Problems */}
      <section className="section-padding bg-white">
        <div className="container-custom">
          <h2 className="heading-2 mb-12 text-center">Common Roof Repair Problems We Fix</h2>

          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6 max-w-5xl mx-auto">
            {commonProblems.map((problem, index) => (
              <div key={index} className="card">
                <h4 className="font-semibold mb-2 flex items-start">
                  <FiCheckCircle className="w-5 h-5 text-teamwork-blue mt-0.5 mr-2 flex-shrink-0" />
                  {problem.title}
                </h4>
                <p className="text-sm text-text-secondary ml-7">{problem.description}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Repair vs Replace */}
      <section className="section-padding bg-light-bg">
        <div className="container-custom">
          <div className="card max-w-3xl mx-auto">
            <h2 className="heading-3 mb-4">Repair vs Replace: We Will Be Honest</h2>
            <p className="text-text-secondary mb-4">
              Sometimes repair makes sense. Sometimes replacement is smarter. We will show you the photos, explain your options, and let you decide.
            </p>
            <p className="text-text-secondary mb-4">
              <strong className="text-text-primary">If your roof has years of life left</strong> and the damage is isolated, we will repair it right and save you money.
            </p>
            <p className="text-text-secondary">
              <strong className="text-text-primary">If it is near the end of its lifespan</strong> or damage is widespread, we will explain why replacement saves you money long-term and prevents repeat repairs.
            </p>
          </div>
        </div>
      </section>

      {/* What Inspection Includes */}
      <section className="section-padding bg-white">
        <div className="container-custom">
          <h2 className="heading-2 mb-12 text-center">What Your Teamwork Inspection Includes</h2>

          <div className="max-w-3xl mx-auto space-y-4">
            <div className="card">
              <h4 className="font-semibold mb-2">Photo Documentation</h4>
              <p className="text-text-secondary text-sm">Detailed photos of all damage so you can see exactly what we see</p>
            </div>
            <div className="card">
              <h4 className="font-semibold mb-2">Written Scope</h4>
              <p className="text-text-secondary text-sm">Clear description of damage and recommended repairs</p>
            </div>
            <div className="card">
              <h4 className="font-semibold mb-2">Clear Pricing</h4>
              <p className="text-text-secondary text-sm">Upfront, honest pricing with no hidden fees</p>
            </div>
            <div className="card">
              <h4 className="font-semibold mb-2">Timeline Estimate</h4>
              <p className="text-text-secondary text-sm">When we can start and how long it will take</p>
            </div>
          </div>
        </div>
      </section>

      {/* Repair Timeline */}
      <section className="section-padding bg-light-bg">
        <div className="container-custom">
          <h2 className="heading-2 mb-12 text-center">Repair Timeline</h2>

          <div className="max-w-3xl mx-auto space-y-4">
            {timeline.map((step, index) => (
              <div key={index} className="flex items-start space-x-4">
                <div className="w-10 h-10 rounded-full bg-teamwork-blue/10 border-2 border-teamwork-blue flex items-center justify-center flex-shrink-0">
                  <span className="text-teamwork-blue font-bold">{index + 1}</span>
                </div>
                <div className="flex items-center h-10">
                  <p className="text-text-secondary">{step}</p>
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      <LocalProjectsSection city={cityData.cityName} />

      <NeighborhoodsSection city={cityData.cityName} neighborhoods={cityData.neighborhoods} />

      {/* Warranty */}
      <section className="section-padding bg-white">
        <div className="container-custom">
          <div className="card max-w-3xl mx-auto text-center">
            <FiShield className="w-12 h-12 text-teamwork-blue mx-auto mb-4" />
            <h3 className="heading-3 mb-4">Repairs Backed by Teamwork Warranty</h3>
            <p className="text-text-secondary mb-6">
              Our repair work is covered under our Teamwork Warranty. Quality workmanship, clean site practices, and your peace of mind.
            </p>
            <Link href="/warranty/" className="text-teamwork-blue hover:underline">
              Learn About Our Warranty →
            </Link>
          </div>
        </div>
      </section>

      {/* FAQ */}
      <section className="section-padding bg-light-bg">
        <div className="container-custom">
          <h2 className="heading-2 mb-12 text-center">Roof Repair FAQ</h2>

          <div className="max-w-3xl mx-auto space-y-4">
            {faqs.map((faq, index) => (
              <div key={index} className="card">
                <h4 className="font-semibold mb-2">{faq.q}</h4>
                <p className="text-text-secondary text-sm">{faq.a}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      <CTABand title={`Need Roof Repair in ${cityData.cityName}?`} subtitle="Call, text, or book your same-week inspection now" />
    </>
  )
}
