import Link from 'next/link'
import { FiCheckCircle, FiAlertTriangle, FiDollarSign } from 'react-icons/fi'
import PromiseStrip from '@/components/PromiseStrip'
import CTABand from '@/components/CTABand'
import { cities } from '@/content/cities'

export const metadata = {
  title: 'Roofing Companies Leawood, KS | How to Compare | Teamwork',
  description: 'Choosing between roofing companies in Leawood? Learn how to compare quotes apples-to-apples, spot red flags, and select the right partner.',
}

const cityData = cities['leawood-ks']

export default function RoofingCompaniesPage() {
  const comparisonPoints = [
    'Scope clarity - What exactly is included?',
    'Material specifications - Brand, product line, warranty length',
    'Underlayment and ice/water protection details',
    'Ventilation upgrades included or extra?',
    'Cleanup and site protection practices',
    'Workmanship warranty terms and length',
    'Timeline - start date and completion estimate',
    'Payment terms and financing options'
  ]

  const redFlags = [
    {
      title: 'No written scope or contract',
      description: 'Everything should be documented in writing before work begins'
    },
    {
      title: 'Pressure to sign today',
      description: 'Quality contractors respect your decision timeline'
    },
    {
      title: 'Requires full payment upfront',
      description: 'Standard practice is deposit, progress payments, and final payment upon completion'
    },
    {
      title: 'No insurance verification',
      description: 'Always verify current liability and workers comp insurance'
    },
    {
      title: 'Vague warranty terms',
      description: 'Workmanship and material warranties should be clear and in writing'
    },
    {
      title: 'No local references',
      description: 'Established contractors have local project history'
    }
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
            <span className="text-text-secondary">Choosing a Company</span>
          </div>
        </div>
      </div>

      <section className="section-padding bg-light-bg">
        <div className="container-custom">
          <div className="max-w-3xl mx-auto text-center">
            <h1 className="heading-1 mb-6">
              Choosing Between Roofing Companies in <span className="text-teamwork-green">{cityData.cityName}</span>
            </h1>
            <p className="text-xl text-text-secondary mb-8">
              Not all roofing companies operate the same way. Learn how to compare quotes apples-to-apples, spot red flags, and select the right partner for your {cityData.cityName} home.
            </p>
            <div className="flex flex-col sm:flex-row gap-4 justify-center">
              <Link href="/book/" className="btn-primary">Book Inspection</Link>
              <Link href="/estimate/" className="btn-secondary">Get Estimate</Link>
            </div>
          </div>
        </div>
      </section>

      <PromiseStrip />

      <section className="section-padding bg-white">
        <div className="container-custom">
          <h2 className="heading-2 mb-12 text-center">How to Compare Quotes Apples-to-Apples</h2>
          <div className="max-w-3xl mx-auto">
            <p className="text-text-secondary mb-8 text-center">
              Price alone does not tell the whole story. Compare these details across every quote:
            </p>
            <div className="space-y-3">
              {comparisonPoints.map((point, index) => (
                <div key={index} className="card">
                  <div className="flex items-start">
                    <FiCheckCircle className="w-5 h-5 text-teamwork-green mt-0.5 mr-3 flex-shrink-0" />
                    <span className="text-text-secondary">{point}</span>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </section>

      <section className="section-padding bg-light-bg">
        <div className="container-custom">
          <h2 className="heading-2 mb-12 text-center">Red Flags to Watch For</h2>
          <div className="grid md:grid-cols-2 gap-6 max-w-5xl mx-auto">
            {redFlags.map((flag, index) => (
              <div key={index} className="card border-red-500/20">
                <div className="flex items-start mb-2">
                  <FiAlertTriangle className="w-5 h-5 text-red-500 mt-0.5 mr-3 flex-shrink-0" />
                  <h4 className="font-semibold text-red-500">{flag.title}</h4>
                </div>
                <p className="text-sm text-text-secondary ml-8">{flag.description}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      <section className="section-padding bg-white">
        <div className="container-custom">
          <div className="card max-w-3xl mx-auto">
            <h3 className="heading-3 mb-4">Warranty Clarity Matters</h3>
            <p className="text-text-secondary mb-4">
              Understand what is covered and for how long:
            </p>
            <ul className="space-y-3">
              <li className="flex items-start">
                <FiCheckCircle className="w-5 h-5 text-teamwork-green mt-0.5 mr-3 flex-shrink-0" />
                <span className="text-text-secondary"><strong className="text-text-primary">Workmanship warranty:</strong> Covers installation errors and labor issues</span>
              </li>
              <li className="flex items-start">
                <FiCheckCircle className="w-5 h-5 text-teamwork-green mt-0.5 mr-3 flex-shrink-0" />
                <span className="text-text-secondary"><strong className="text-text-primary">Material warranty:</strong> Manufacturer coverage on shingles (typically 25 years to lifetime)</span>
              </li>
              <li className="flex items-start">
                <FiCheckCircle className="w-5 h-5 text-teamwork-green mt-0.5 mr-3 flex-shrink-0" />
                <span className="text-text-secondary"><strong className="text-text-primary">Transferability:</strong> Can warranty transfer if you sell your home?</span>
              </li>
            </ul>
            <p className="text-sm text-text-muted mt-6">
              At Teamwork, our Teamwork Warranty covers workmanship, and manufacturer warranties cover materials. We explain both clearly before you sign.
            </p>
          </div>
        </div>
      </section>

      <section className="section-padding bg-light-bg">
        <div className="container-custom">
          <div className="card max-w-3xl mx-auto">
            <FiDollarSign className="w-12 h-12 text-teamwork-green mx-auto mb-4" />
            <h3 className="heading-3 mb-4 text-center">Financing Considerations</h3>
            <p className="text-text-secondary mb-4 text-center">
              Most {cityData.cityName} homeowners use financing for roof replacement. Ask each company:
            </p>
            <ul className="space-y-3 max-w-xl mx-auto">
              <li className="flex items-start">
                <FiCheckCircle className="w-5 h-5 text-teamwork-green mt-0.5 mr-3 flex-shrink-0" />
                <span className="text-text-secondary">Do you offer financing or partner with lenders?</span>
              </li>
              <li className="flex items-start">
                <FiCheckCircle className="w-5 h-5 text-teamwork-green mt-0.5 mr-3 flex-shrink-0" />
                <span className="text-text-secondary">What are the typical terms and rates?</span>
              </li>
              <li className="flex items-start">
                <FiCheckCircle className="w-5 h-5 text-teamwork-green mt-0.5 mr-3 flex-shrink-0" />
                <span className="text-text-secondary">Are there deferred interest or low-rate options?</span>
              </li>
            </ul>
            <p className="text-sm text-text-muted text-center mt-6">
              Teamwork offers flexible financing options with multiple term lengths. <Link href="/financing/" className="text-teamwork-green hover:underline">Learn more about financing</Link>
            </p>
          </div>
        </div>
      </section>

      <section className="section-padding bg-white">
        <div className="container-custom">
          <div className="max-w-3xl mx-auto text-center">
            <h2 className="heading-2 mb-6">Why Teamwork</h2>
            <p className="text-text-secondary mb-8">
              We compete on transparency, not tricks. Photo-proof documentation, clean site guarantee, honest guidance, and partnership from day one.
            </p>
            <p className="text-text-secondary mb-8">
              Compare us to any {cityData.cityName} roofing company - we welcome the opportunity to earn your trust.
            </p>
            <div className="flex flex-col sm:flex-row gap-4 justify-center">
              <Link href="/book/" className="btn-primary">Book Inspection</Link>
              <a href={`tel:${cityData.phone}`} className="btn-secondary">Call {cityData.phone}</a>
            </div>
          </div>
        </div>
      </section>

      <CTABand title="Ready to Compare?" subtitle={`Get a Teamwork inspection and see the difference transparency makes`} />
    </>
  )
}
