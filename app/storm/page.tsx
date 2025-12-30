import Link from 'next/link'
import { FiCheckCircle, FiCamera, FiClipboard } from 'react-icons/fi'
import PromiseStrip from '@/components/PromiseStrip'
import CTABand from '@/components/CTABand'

export const metadata = {
  title: 'Storm Damage Inspection Kansas City | Teamwork Roofing',
  description: 'Professional storm damage inspection and documentation in Kansas City Metro. Full exterior assessment: roof, gutters, siding, windows.',
}

export default function StormPage() {
  return (
    <>
      <section className="section-padding bg-dark-bg">
        <div className="container-custom">
          <div className="max-w-3xl">
            <h1 className="heading-1 mb-6">
              Storm Damage? <span className="text-teamwork-blue">Start With Teamwork</span>
            </h1>
            <p className="text-xl text-gray-400 mb-8">
              Full exterior storm assessment with professional photo documentation you can share with your insurer and adjuster.
            </p>
            <div className="flex flex-wrap gap-4">
              <Link href="/book/" className="btn-primary">Book Storm Inspection</Link>
              <a href="tel:9133963717" className="btn-secondary">Call 913-396-3717</a>
            </div>
          </div>
        </div>
      </section>

      <PromiseStrip />

      <section className="section-padding bg-dark-surface">
        <div className="container-custom">
          <h2 className="heading-2 mb-12 text-center">Full Exterior Storm Check</h2>
          <p className="text-xl text-gray-400 text-center mb-8 max-w-3xl mx-auto">
            We inspect every exterior surface storms commonly impact — so nothing gets missed.
          </p>
          <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-6 max-w-4xl mx-auto">
            <div className="card text-center">
              <h4 className="font-semibold mb-2">Roof</h4>
              <p className="text-sm text-gray-400">Shingle damage, missing granules, impact marks</p>
            </div>
            <div className="card text-center">
              <h4 className="font-semibold mb-2">Gutters</h4>
              <p className="text-sm text-gray-400">Dents, detachment, downspout damage</p>
            </div>
            <div className="card text-center">
              <h4 className="font-semibold mb-2">Siding</h4>
              <p className="text-sm text-gray-400">Cracks, holes, hail impact, wind damage</p>
            </div>
            <div className="card text-center">
              <h4 className="font-semibold mb-2">Windows</h4>
              <p className="text-sm text-gray-400">Broken glass, frame damage, seal failure</p>
            </div>
          </div>
        </div>
      </section>

      <section className="section-padding bg-dark-bg">
        <div className="container-custom">
          <h2 className="heading-2 mb-12 text-center">Photo Documentation</h2>
          <div className="card max-w-3xl mx-auto">
            <FiCamera className="w-12 h-12 text-teamwork-blue mb-4 mx-auto" />
            <h3 className="heading-4 mb-4 text-center">What You Get From Teamwork</h3>
            <ul className="space-y-3 mb-6">
              <li className="flex items-start space-x-3">
                <FiCheckCircle className="w-5 h-5 text-teamwork-blue mt-1 flex-shrink-0" />
                <span className="text-gray-300">Detailed photos of visible exterior damage and affected areas</span>
              </li>
              <li className="flex items-start space-x-3">
                <FiCheckCircle className="w-5 h-5 text-teamwork-blue mt-1 flex-shrink-0" />
                <span className="text-gray-300">A written scope of observed damage and recommended repairs</span>
              </li>
              <li className="flex items-start space-x-3">
                <FiCheckCircle className="w-5 h-5 text-teamwork-blue mt-1 flex-shrink-0" />
                <span className="text-gray-300">A repair estimate for your records and to share with your insurer/adjuster</span>
              </li>
              <li className="flex items-start space-x-3">
                <FiCheckCircle className="w-5 h-5 text-teamwork-blue mt-1 flex-shrink-0" />
                <span className="text-gray-300">On-site availability during the adjuster visit (at your request) to answer construction questions about materials, code-related items, and repair methods</span>
              </li>
            </ul>
            <div className="bg-dark-bg border border-dark-border rounded-lg p-4">
              <p className="text-sm text-gray-400 font-semibold mb-2">Important (Kansas + Missouri):</p>
              <p className="text-sm text-gray-500">
                We provide inspection documentation and repair estimates. We are not public adjusters, do not negotiate or settle claims, and do not interpret policy coverage or guarantee claim outcomes.
              </p>
            </div>
          </div>
        </div>
      </section>

      <section className="section-padding bg-dark-surface">
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
                <div className="w-10 h-10 rounded-full bg-teamwork-blue/10 border-2 border-teamwork-blue flex items-center justify-center flex-shrink-0">
                  <span className="text-teamwork-blue font-bold">{index + 1}</span>
                </div>
                <div className="flex items-center h-10">
                  <p className="text-gray-300">{step}</p>
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      <CTABand title="Storm Damage? Act Fast" subtitle="Book your full exterior inspection today" />
    </>
  )
}
