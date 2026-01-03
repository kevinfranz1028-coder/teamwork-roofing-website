import Link from 'next/link'
import { FiCheckCircle, FiCamera, FiClipboard } from 'react-icons/fi'
import PromiseStrip from '@/components/PromiseStrip'
import CTABand from '@/components/CTABand'
import BrandsWeInstall from '@/components/BrandsWeInstall'

export const metadata = {
  title: 'Storm Damage Inspection Kansas City | Teamwork Roofing',
  description: 'Professional storm damage inspection and documentation in Kansas City Metro. Full exterior assessment: roof, gutters, siding, windows.',
}

export default function StormPage() {
  return (
    <>
      <section className="section-padding bg-light-bg">
        <div className="container-custom">
          <div className="max-w-3xl">
            <h1 className="heading-1 mb-6">
              Storm Damage? <span className="text-teamwork-green">Start With Teamwork</span>
            </h1>
            <p className="text-xl text-text-secondary mb-4">
              Full exterior storm assessment with professional photo documentation you can share with your insurer and adjuster.
            </p>
            <p className="text-sm text-text-secondary mb-8">
              <Link href="/service-areas/" className="hover:text-teamwork-green hover:underline transition-colors">
                Storm inspection by city →
              </Link>
            </p>
            <div className="flex flex-wrap gap-4">
              <Link href="/book/" className="btn-primary">Book Storm Inspection</Link>
              <a href="tel:9133963717" className="btn-secondary">Call 913-396-3717</a>
            </div>
          </div>
        </div>
      </section>

      <PromiseStrip />

      <section className="section-padding bg-white">
        <div className="container-custom">
          <h2 className="heading-2 mb-12 text-center">Full Exterior Storm Check</h2>
          <p className="text-xl text-text-secondary text-center mb-8 max-w-3xl mx-auto">
            We inspect every exterior surface storms commonly impact — so nothing gets missed.
          </p>
          <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-6 max-w-4xl mx-auto">
            <div className="card text-center">
              <h4 className="font-semibold mb-2">Roof</h4>
              <p className="text-sm text-text-secondary">Shingle damage, missing granules, impact marks</p>
            </div>
            <div className="card text-center">
              <h4 className="font-semibold mb-2">Gutters</h4>
              <p className="text-sm text-text-secondary">Dents, detachment, downspout damage</p>
            </div>
            <div className="card text-center">
              <h4 className="font-semibold mb-2">Siding</h4>
              <p className="text-sm text-text-secondary">Cracks, holes, hail impact, wind damage</p>
            </div>
            <div className="card text-center">
              <h4 className="font-semibold mb-2">Windows</h4>
              <p className="text-sm text-text-secondary">Broken glass, frame damage, seal failure</p>
            </div>
          </div>
        </div>
      </section>

      <section className="section-padding bg-light-bg">
        <div className="container-custom">
          <h2 className="heading-2 mb-12 text-center">Photo Documentation</h2>
          <div className="card max-w-3xl mx-auto">
            <FiCamera className="w-12 h-12 text-teamwork-green mb-4 mx-auto" />
            <h3 className="heading-4 mb-4 text-center">What You Get From Teamwork</h3>
            <ul className="space-y-3 mb-6">
              <li className="flex items-start space-x-3">
                <FiCheckCircle className="w-5 h-5 text-teamwork-green mt-1 flex-shrink-0" />
                <span className="text-text-secondary">Detailed photos of visible exterior damage and affected areas</span>
              </li>
              <li className="flex items-start space-x-3">
                <FiCheckCircle className="w-5 h-5 text-teamwork-green mt-1 flex-shrink-0" />
                <span className="text-text-secondary">A written scope of observed damage and recommended repairs</span>
              </li>
              <li className="flex items-start space-x-3">
                <FiCheckCircle className="w-5 h-5 text-teamwork-green mt-1 flex-shrink-0" />
                <span className="text-text-secondary">A repair estimate for your records and to share with your insurer/adjuster</span>
              </li>
              <li className="flex items-start space-x-3">
                <FiCheckCircle className="w-5 h-5 text-teamwork-green mt-1 flex-shrink-0" />
                <span className="text-text-secondary">On-site availability during the adjuster visit (at your request) to answer construction questions about materials, code-related items, and repair methods</span>
              </li>
            </ul>
            <div className="bg-light-bg border border-light-border rounded-lg p-4">
              <p className="text-sm text-text-secondary font-semibold mb-2">Important (Kansas + Missouri):</p>
              <p className="text-sm text-text-muted">
                We provide inspection documentation and repair estimates. We are not public adjusters, do not negotiate or settle claims, and do not interpret policy coverage or guarantee claim outcomes.
              </p>
            </div>
          </div>
        </div>
      </section>

      <section className="section-padding bg-white">
        <div className="container-custom">
          <h2 className="heading-2 mb-12 text-center">What To Do Now</h2>
          <div className="max-w-3xl mx-auto space-y-4">
            {[
              'Contact your insurance company to file a claim',
              'Book your same-week inspection with us',
              'Take your own photos as initial documentation',
              'Keep damaged materials if safe to do so',
              'Review your policy coverage and deductible',
              'Schedule the adjuster inspection (we can be on-site if you want us there)'
            ].map((step, index) => (
              <div key={index} className="flex items-start space-x-4">
                <div className="w-10 h-10 rounded-full bg-teamwork-green/10 border-2 border-teamwork-green flex items-center justify-center flex-shrink-0">
                  <span className="text-teamwork-green font-bold">{index + 1}</span>
                </div>
                <div className="flex items-center h-10">
                  <p className="text-text-secondary">{step}</p>
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Brands We Install */}
      <BrandsWeInstall variant="compact" />

      <CTABand title="Storm Damage? Act Fast" subtitle="Book your full exterior inspection today" />
    </>
  )
}
