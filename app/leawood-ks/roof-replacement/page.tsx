import Link from 'next/link'
import { FiCheckCircle, FiShield } from 'react-icons/fi'
import PromiseStrip from '@/components/PromiseStrip'
import CTABand from '@/components/CTABand'
import BrandsWeInstall from '@/components/BrandsWeInstall'
import { cities } from '@/content/cities'

export const metadata = {
  title: 'Roof Replacement Leawood, KS | Warranty + Clean Site | Teamwork',
  description: 'Professional roof replacement in Leawood. Photo-proof inspection, clean site guarantee, financing, Teamwork Warranty. Same-week inspections.',
}

const cityData = cities['leawood-ks']

export default function RoofReplacementPage() {
  const signs = [
    'Shingles are 20+ years old',
    'Multiple leak areas or frequent repairs',
    'Widespread granule loss or curling',
    'Missing shingles after wind events',
    'Visible sagging or structural issues',
    'Failed inspection or appraisal concerns'
  ]

  const process = [
    { title: 'Photo-Proof Inspection', description: 'Detailed photos of your current roof condition' },
    { title: 'Material Selection', description: 'Choose from manufacturer-grade systems to fit your home and budget' },
    { title: 'Clean Site Prep', description: 'Tarps, dumpster placement, and landscape protection' },
    { title: 'Professional Installation', description: 'Experienced crew following manufacturer specifications' },
    { title: 'Daily Cleanup & Final Walk', description: 'Magnetic sweeps, debris removal, and your approval' },
    { title: 'Warranty Activation', description: 'Teamwork Warranty on workmanship plus manufacturer coverage' }
  ]

  return (
    <>
      <div className="bg-white border-b border-light-border">
        <div className="container-custom py-4">
          <div className="flex items-center space-x-2 text-sm text-text-muted">
            <Link href="/" className="hover:text-teamwork-blue">Home</Link>
            <span>/</span>
            <Link href={`/${cityData.slug}/`} className="hover:text-teamwork-blue">{cityData.cityName}</Link>
            <span>/</span>
            <span className="text-text-secondary">Roof Replacement</span>
          </div>
        </div>
      </div>

      <section className="section-padding bg-light-bg">
        <div className="container-custom">
          <div className="max-w-3xl">
            <h1 className="heading-1 mb-6">
              Roof Replacement in <span className="text-teamwork-blue">{cityData.cityName}, {cityData.state}</span>
            </h1>
            <p className="text-xl text-text-secondary mb-8">
              Professional roof replacement with photo-proof documentation, clean site practices, and Teamwork Warranty backing. Serving all {cityData.cityName} neighborhoods with same-week inspections.
            </p>
            <div className="flex flex-wrap gap-4">
              <Link href="/book/" className="btn-primary">Book Inspection</Link>
              <Link href="/estimate/" className="btn-secondary">Get Estimate</Link>
            </div>
          </div>
        </div>
      </section>

      <PromiseStrip />

      <section className="section-padding bg-white">
        <div className="container-custom">
          <h2 className="heading-2 mb-12 text-center">Signs You Need Roof Replacement</h2>
          <div className="grid md:grid-cols-2 gap-4 max-w-3xl mx-auto">
            {signs.map((sign, index) => (
              <div key={index} className="flex items-start space-x-3">
                <FiCheckCircle className="w-5 h-5 text-teamwork-blue mt-1 flex-shrink-0" />
                <span className="text-text-secondary">{sign}</span>
              </div>
            ))}
          </div>
          <p className="text-center text-text-muted text-sm mt-8 max-w-2xl mx-auto">
            Not sure if you need replacement? We will show you photos during inspection and give honest guidance.
          </p>
        </div>
      </section>

      <section className="section-padding bg-light-bg">
        <div className="container-custom">
          <h2 className="heading-2 mb-12 text-center">The Teamwork Replacement Process</h2>
          <div className="max-w-3xl mx-auto space-y-4">
            {process.map((step, index) => (
              <div key={index} className="card">
                <div className="flex items-start space-x-4">
                  <div className="w-10 h-10 rounded-full bg-teamwork-blue/10 border-2 border-teamwork-blue flex items-center justify-center flex-shrink-0">
                    <span className="text-teamwork-blue font-bold">{index + 1}</span>
                  </div>
                  <div>
                    <h4 className="font-semibold mb-1">{step.title}</h4>
                    <p className="text-sm text-text-secondary">{step.description}</p>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      <section className="section-padding bg-white">
        <div className="container-custom">
          <div className="card max-w-3xl mx-auto">
            <h3 className="heading-3 mb-4">Ventilation & Water Management Built In</h3>
            <p className="text-text-secondary mb-4">
              Proper roof ventilation and water protection are non-negotiable in {cityData.cityName}. We install:
            </p>
            <ul className="space-y-3">
              <li className="flex items-start">
                <FiCheckCircle className="w-5 h-5 text-teamwork-blue mt-0.5 mr-3 flex-shrink-0" />
                <span className="text-text-secondary">Underlayment protection across the entire roof deck</span>
              </li>
              <li className="flex items-start">
                <FiCheckCircle className="w-5 h-5 text-teamwork-blue mt-0.5 mr-3 flex-shrink-0" />
                <span className="text-text-secondary">Ice and water shield in critical leak-prone areas</span>
              </li>
              <li className="flex items-start">
                <FiCheckCircle className="w-5 h-5 text-teamwork-blue mt-0.5 mr-3 flex-shrink-0" />
                <span className="text-text-secondary">Ridge vents and intake ventilation for proper airflow</span>
              </li>
              <li className="flex items-start">
                <FiCheckCircle className="w-5 h-5 text-teamwork-blue mt-0.5 mr-3 flex-shrink-0" />
                <span className="text-text-secondary">Flashing upgrades around chimneys, vents, and valleys</span>
              </li>
            </ul>
          </div>
        </div>
      </section>

      <BrandsWeInstall variant="compact" />

      <section className="section-padding bg-light-bg">
        <div className="container-custom">
          <div className="card max-w-3xl mx-auto text-center">
            <FiShield className="w-12 h-12 text-teamwork-blue mx-auto mb-4" />
            <h3 className="heading-3 mb-4">Clean Site Workflow</h3>
            <p className="text-text-secondary mb-4">
              Your {cityData.cityName} property is protected before, during, and after installation:
            </p>
            <ul className="text-left space-y-2 text-text-secondary max-w-xl mx-auto">
              <li className="flex items-start">
                <FiCheckCircle className="w-5 h-5 text-teamwork-blue mt-0.5 mr-3 flex-shrink-0" />
                <span>Tarps placed to protect landscaping and gutters</span>
              </li>
              <li className="flex items-start">
                <FiCheckCircle className="w-5 h-5 text-teamwork-blue mt-0.5 mr-3 flex-shrink-0" />
                <span>Dumpster positioned for safe debris containment</span>
              </li>
              <li className="flex items-start">
                <FiCheckCircle className="w-5 h-5 text-teamwork-blue mt-0.5 mr-3 flex-shrink-0" />
                <span>Daily cleanup and magnetic nail sweeps</span>
              </li>
              <li className="flex items-start">
                <FiCheckCircle className="w-5 h-5 text-teamwork-blue mt-0.5 mr-3 flex-shrink-0" />
                <span>Final walkthrough and your approval before we leave</span>
              </li>
            </ul>
          </div>
        </div>
      </section>

      <CTABand title={`Ready for a New Roof in ${cityData.cityName}?`} subtitle="Book your same-week inspection or get a quick estimate today" />
    </>
  )
}
