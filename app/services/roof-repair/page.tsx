import Link from 'next/link'
import { FiCheckCircle, FiPhone, FiMessageSquare } from 'react-icons/fi'
import PromiseStrip from '@/components/PromiseStrip'
import CTABand from '@/components/CTABand'
import BrandsWeInstall from '@/components/BrandsWeInstall'

export const metadata = {
  title: 'Roof Repair Kansas City | Fast Professional Service',
  description: 'Fast roof repair in Kansas City Metro. Same-week service, photo documentation, honest repair vs replace guidance. Call 913-396-3717',
}

export default function RoofRepairPage() {
  const commonIssues = [
    'Missing or damaged shingles',
    'Flashing failures',
    'Vent boot cracks',
    'Storm damage',
    'Active leaks',
    'Chimney flashing issues'
  ]

  const processSteps = [
    'Same-week inspection scheduled',
    'Photo documentation of all damage',
    'Honest repair vs replace assessment',
    'Clear pricing and timeline',
    'Professional repair with clean site',
    'Warranty activation'
  ]

  return (
    <>
      <section className="section-padding bg-dark-bg">
        <div className="container-custom">
          <div className="max-w-3xl">
            <h1 className="heading-1 mb-6">
              Roof Repair — <span className="text-teamwork-blue">Fast, Clean, Photo-Documented</span>
            </h1>
            <p className="text-xl text-gray-400 mb-4">
              Same-week service for Kansas City Metro. Honest guidance on repair vs replace.
            </p>
            <p className="text-sm text-gray-400 mb-8">
              <Link href="/overland-park-ks/roof-repair/" className="hover:text-teamwork-blue hover:underline transition-colors">
                Need roof repair in Overland Park? See local options →
              </Link>
            </p>
            <div className="flex flex-wrap gap-4">
              <a href="tel:9133963717" className="btn-primary">
                <FiPhone className="inline mr-2" />
                Call 913-396-3717
              </a>
              <a href="sms:9133963717" className="btn-secondary">
                <FiMessageSquare className="inline mr-2" />
                Text Us
              </a>
              <Link href="/book/" className="btn-secondary">
                Book Inspection
              </Link>
            </div>
          </div>
        </div>
      </section>

      <PromiseStrip />

      <section className="section-padding bg-dark-surface">
        <div className="container-custom">
          <h2 className="heading-2 mb-12 text-center">Common Issues We Fix</h2>
          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-4 max-w-4xl mx-auto">
            {commonIssues.map((issue, index) => (
              <div key={index} className="flex items-start space-x-3">
                <FiCheckCircle className="w-5 h-5 text-teamwork-blue mt-1 flex-shrink-0" />
                <span className="text-gray-300">{issue}</span>
              </div>
            ))}
          </div>
        </div>
      </section>

      <section className="section-padding bg-dark-bg">
        <div className="container-custom">
          <div className="card max-w-3xl mx-auto">
            <h2 className="heading-3 mb-4">Repair vs Replace: We'll Be Honest</h2>
            <p className="text-gray-400 mb-4">
              Sometimes repair makes sense. Sometimes replacement is smarter. We'll show you the photos, explain your options, and let you decide.
            </p>
            <p className="text-gray-400">
              If your roof has years of life left, we'll repair it right. If it's near the end, we'll explain why replacement saves you money long-term.
            </p>
          </div>
        </div>
      </section>

      <section className="section-padding bg-dark-surface">
        <div className="container-custom">
          <h2 className="heading-2 mb-12 text-center">Our Repair Process</h2>
          <div className="max-w-3xl mx-auto space-y-4">
            {processSteps.map((step, index) => (
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

      {/* Brands We Install */}
      <BrandsWeInstall variant="compact" />

      <CTABand title="Need Roof Repair Fast?" subtitle="Call, text, or book your same-week inspection now" />
    </>
  )
}
