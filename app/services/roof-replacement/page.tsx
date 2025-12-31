import Link from 'next/link'
import { FiCheckCircle, FiDollarSign, FiShield, FiClock } from 'react-icons/fi'
import PromiseStrip from '@/components/PromiseStrip'
import CTABand from '@/components/CTABand'
import BrandsWeInstall from '@/components/BrandsWeInstall'

export const metadata = {
  title: 'Roof Replacement Kansas City | Teamwork Roofing Services',
  description: 'Premium roof replacement services in Kansas City Metro. Same-week inspections, photo documentation, financing available. Licensed & insured.',
}

export default function RoofReplacementPage() {
  const signs = [
    'Shingles curling, cracking, or missing',
    'Roof age over 20 years',
    'Widespread granule loss',
    'Multiple leak points',
    'Sagging or visible damage',
    'Failed previous repairs'
  ]

  const tiers = [
    {
      name: 'Good',
      description: 'Reliable protection, budget-friendly',
      features: ['3-tab shingles', '25-year warranty', 'Standard ventilation', 'Quality installation']
    },
    {
      name: 'Better',
      description: 'Enhanced durability and curb appeal',
      features: ['Architectural shingles', '30-50 year warranty', 'Improved ventilation', 'Premium underlayment']
    },
    {
      name: 'Best',
      description: 'Maximum protection and aesthetics',
      features: ['Designer shingles', 'Lifetime warranty', 'Advanced ventilation', 'Complete system upgrade']
    }
  ]

  const processSteps = [
    { title: 'Same-Week Inspection', description: 'Full roof assessment with photo documentation' },
    { title: 'Material Selection', description: 'Review options that fit your needs and budget' },
    { title: 'Financing Review', description: 'Explore Teamwork Financing if needed' },
    { title: 'Professional Installation', description: 'Expert crew with clean site practices' },
    { title: 'Final Walkthrough', description: 'Ensure satisfaction and activate warranty' }
  ]

  const pricingFactors = [
    'Roof size and pitch',
    'Material selection',
    'Number of penetrations (vents, chimneys)',
    'Structural repairs needed',
    'Accessibility',
    'Permit and disposal fees'
  ]

  const faqs = [
    {
      q: 'How long does a roof replacement take?',
      a: 'Most residential roof replacements take 1-3 days, depending on size and complexity.'
    },
    {
      q: 'Do you handle permits?',
      a: 'Yes, we handle all necessary permits as part of our service.'
    },
    {
      q: 'What warranty do you offer?',
      a: 'Manufacturer warranties range from 25 years to lifetime, plus our Teamwork Warranty on installation.'
    },
    {
      q: 'Can I get financing?',
      a: 'Yes, we offer Teamwork Financing options to fit your budget.'
    },
    {
      q: 'Will you protect my property?',
      a: 'Absolutely. Our Clean Site Guarantee includes tarps, careful material handling, and thorough cleanup.'
    }
  ]

  return (
    <>
      {/* Hero */}
      <section className="section-padding bg-dark-bg">
        <div className="container-custom">
          <div className="max-w-3xl">
            <h1 className="heading-1 mb-6">
              Roof Replacement — <span className="text-teamwork-blue">The Teamwork Way</span>
            </h1>
            <p className="text-xl text-gray-400 mb-8">
              Premium materials, expert installation, photo documentation, and financing options for Kansas City Metro homeowners
            </p>
            <div className="flex flex-wrap gap-4">
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

      <PromiseStrip />

      {/* Signs You Need Replacement */}
      <section className="section-padding bg-dark-surface">
        <div className="container-custom">
          <h2 className="heading-2 mb-12 text-center">Signs You Need Roof Replacement</h2>
          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-4 max-w-4xl mx-auto">
            {signs.map((sign, index) => (
              <div key={index} className="flex items-start space-x-3">
                <FiCheckCircle className="w-5 h-5 text-teamwork-blue mt-1 flex-shrink-0" />
                <span className="text-gray-300">{sign}</span>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Material Tiers */}
      <section className="section-padding bg-dark-bg">
        <div className="container-custom">
          <h2 className="heading-2 mb-4 text-center">Good, Better, Best</h2>
          <p className="text-xl text-gray-400 text-center mb-12">Choose the option that fits your needs</p>

          <div className="grid md:grid-cols-3 gap-8">
            {tiers.map((tier, index) => (
              <div key={index} className="card">
                <h3 className="heading-3 mb-2">{tier.name}</h3>
                <p className="text-gray-400 mb-6">{tier.description}</p>
                <ul className="space-y-3">
                  {tier.features.map((feature, idx) => (
                    <li key={idx} className="flex items-start space-x-2">
                      <FiCheckCircle className="w-5 h-5 text-teamwork-blue mt-0.5 flex-shrink-0" />
                      <span className="text-sm text-gray-300">{feature}</span>
                    </li>
                  ))}
                </ul>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Process */}
      <section className="section-padding bg-dark-surface">
        <div className="container-custom">
          <h2 className="heading-2 mb-12 text-center">The Teamwork Process</h2>
          <div className="max-w-3xl mx-auto space-y-6">
            {processSteps.map((step, index) => (
              <div key={index} className="flex items-start space-x-4">
                <div className="w-10 h-10 rounded-full bg-teamwork-blue/10 border-2 border-teamwork-blue flex items-center justify-center flex-shrink-0">
                  <span className="text-teamwork-blue font-bold">{index + 1}</span>
                </div>
                <div>
                  <h4 className="font-semibold mb-1">{step.title}</h4>
                  <p className="text-gray-400 text-sm">{step.description}</p>
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Pricing Factors */}
      <section className="section-padding bg-dark-bg">
        <div className="container-custom">
          <h2 className="heading-2 mb-4 text-center">What Affects Pricing</h2>
          <p className="text-xl text-gray-400 text-center mb-12">
            Every roof is different — here's what we consider
          </p>

          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-4 max-w-4xl mx-auto">
            {pricingFactors.map((factor, index) => (
              <div key={index} className="card text-center">
                <p className="text-gray-300">{factor}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Financing Teaser */}
      <section className="section-padding bg-dark-surface">
        <div className="container-custom">
          <div className="card max-w-3xl mx-auto text-center">
            <FiDollarSign className="w-12 h-12 text-teamwork-blue mx-auto mb-4" />
            <h2 className="heading-3 mb-4">Teamwork Financing Available</h2>
            <p className="text-gray-400 mb-6">
              Flexible payment options to make your roof replacement affordable
            </p>
            <Link href="/financing/" className="btn-primary">
              Learn About Financing
            </Link>
          </div>
        </div>
      </section>

      {/* Brands We Install */}
      <BrandsWeInstall variant="compact" />

      {/* FAQ */}
      <section className="section-padding bg-dark-bg">
        <div className="container-custom">
          <h2 className="heading-2 mb-12 text-center">Roof Replacement FAQ</h2>
          <div className="max-w-3xl mx-auto space-y-4">
            {faqs.map((faq, index) => (
              <div key={index} className="card">
                <h4 className="font-semibold mb-2">{faq.q}</h4>
                <p className="text-gray-400 text-sm">{faq.a}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      <CTABand title="Ready for a New Roof?" subtitle="Book your same-week inspection or get a quick estimate" />
    </>
  )
}
