import Link from 'next/link'
import { FiPhone, FiMessageSquare, FiCheckCircle, FiAlertCircle } from 'react-icons/fi'
import PromiseStrip from '@/components/PromiseStrip'
import CTABand from '@/components/CTABand'

export const metadata = {
  title: 'Emergency Roof Repair Overland Park | Call/Text Now | Teamwork',
  description: 'Emergency roof repair in Overland Park, KS. Active leaks, storm damage, urgent repairs. Same-day response. Call or text 913-396-3717 now.',
}

export default function EmergencyRoofRepairPage() {
  return (
    <>
      <div className="bg-white border-b border-light-border">
        <div className="container-custom py-4">
          <div className="flex items-center space-x-2 text-sm text-text-muted">
            <Link href="/" className="hover:text-teamwork-blue">Home</Link>
            <span>/</span>
            <Link href="/overland-park-ks/" className="hover:text-teamwork-blue">Overland Park</Link>
            <span>/</span>
            <span className="text-text-secondary">Emergency Roof Repair</span>
          </div>
        </div>
      </div>

      <section className="section-padding bg-light-bg">
        <div className="container-custom">
          <div className="max-w-3xl mx-auto text-center">
            <div className="inline-flex items-center space-x-2 bg-red-500/10 border border-red-500 px-4 py-2 rounded-lg mb-6">
              <FiAlertCircle className="w-5 h-5 text-red-500" />
              <span className="text-red-500 font-semibold">Emergency Service Available</span>
            </div>
            <h1 className="heading-1 mb-6">Emergency Roof Repair in Overland Park</h1>
            <p className="text-xl text-text-secondary mb-8">
              Active leak? Storm damage? We respond fast in Overland Park. Call or text now for same-day emergency service.
            </p>

            <div className="flex flex-col sm:flex-row gap-4 justify-center mb-8">
              <a href="tel:9133963717" className="btn-primary text-lg">
                <FiPhone className="inline mr-2" />
                Call Now: 913-396-3717
              </a>
              <a href="sms:9133963717" className="btn-primary bg-green-600 hover:bg-green-700 text-lg">
                <FiMessageSquare className="inline mr-2" />
                Text: 913-396-3717
              </a>
            </div>

            <div className="flex flex-wrap gap-4 justify-center">
              <Link href="/book/" className="btn-secondary">Book Inspection</Link>
              <Link href="/estimate/" className="btn-secondary">Get Estimate</Link>
            </div>
          </div>
        </div>
      </section>

      <PromiseStrip />

      <section className="section-padding bg-white">
        <div className="container-custom">
          <h2 className="heading-2 mb-12 text-center">2-Minute Emergency Checklist</h2>
          <div className="max-w-3xl mx-auto card bg-yellow-500/5 border-yellow-500">
            <ol className="space-y-4">
              <li className="flex items-start space-x-3">
                <span className="font-bold text-yellow-500">1.</span>
                <span className="text-text-secondary">Safety first - If water is near electrical, turn off power to that area</span>
              </li>
              <li className="flex items-start space-x-3">
                <span className="font-bold text-yellow-500">2.</span>
                <span className="text-text-secondary">Place buckets under active leaks</span>
              </li>
              <li className="flex items-start space-x-3">
                <span className="font-bold text-yellow-500">3.</span>
                <span className="text-text-secondary">Move valuables away from leak areas</span>
              </li>
              <li className="flex items-start space-x-3">
                <span className="font-bold text-yellow-500">4.</span>
                <span className="text-text-secondary">Take photos of damage (interior and visible exterior)</span>
              </li>
              <li className="flex items-start space-x-3">
                <span className="font-bold text-yellow-500">5.</span>
                <span className="text-text-secondary">Call or text us immediately: 913-396-3717</span>
              </li>
            </ol>
            <p className="text-text-secondary text-sm text-center mt-6">
              Need non-emergency help? <Link href="/overland-park-ks/roof-repair/" className="text-teamwork-blue hover:underline">See Roof Repair in Overland Park →</Link>
            </p>
          </div>
        </div>
      </section>

      <section className="section-padding bg-light-bg">
        <div className="container-custom">
          <h2 className="heading-2 mb-12 text-center">Text Us Photos</h2>
          <div className="max-w-3xl mx-auto">
            <p className="text-text-secondary mb-6 text-center">Text photos to 913-396-3717. Include:</p>
            <div className="grid md:grid-cols-2 gap-6">
              <div className="card">
                <h4 className="font-semibold mb-3">Interior Photos</h4>
                <ul className="space-y-2 text-sm text-text-secondary">
                  <li className="flex items-start"><FiCheckCircle className="w-4 h-4 text-teamwork-blue mt-1 mr-2 flex-shrink-0" />Water stains on ceiling</li>
                  <li className="flex items-start"><FiCheckCircle className="w-4 h-4 text-teamwork-blue mt-1 mr-2 flex-shrink-0" />Active dripping areas</li>
                  <li className="flex items-start"><FiCheckCircle className="w-4 h-4 text-teamwork-blue mt-1 mr-2 flex-shrink-0" />Wet insulation if visible</li>
                </ul>
              </div>
              <div className="card">
                <h4 className="font-semibold mb-3">Exterior Photos (if safe)</h4>
                <ul className="space-y-2 text-sm text-text-secondary">
                  <li className="flex items-start"><FiCheckCircle className="w-4 h-4 text-teamwork-blue mt-1 mr-2 flex-shrink-0" />Visible roof damage</li>
                  <li className="flex items-start"><FiCheckCircle className="w-4 h-4 text-teamwork-blue mt-1 mr-2 flex-shrink-0" />Missing shingles</li>
                  <li className="flex items-start"><FiCheckCircle className="w-4 h-4 text-teamwork-blue mt-1 mr-2 flex-shrink-0" />General overview</li>
                </ul>
              </div>
            </div>
          </div>
        </div>
      </section>

      <section className="section-padding bg-white">
        <div className="container-custom">
          <h2 className="heading-2 mb-12 text-center">What We Can Do Fast</h2>
          <div className="max-w-4xl mx-auto grid md:grid-cols-2 gap-8">
            <div className="card">
              <h4 className="font-semibold mb-3 text-green-500">Temporary Mitigation</h4>
              <p className="text-text-secondary text-sm mb-4">Stop or slow active water intrusion:</p>
              <ul className="space-y-2 text-sm text-text-secondary">
                <li>Tarp installation</li>
                <li>Emergency patching</li>
                <li>Temporary sealing</li>
              </ul>
            </div>
            <div className="card">
              <h4 className="font-semibold mb-3 text-teamwork-blue">Permanent Repair</h4>
              <p className="text-text-secondary text-sm mb-4">Once assessed and approved:</p>
              <ul className="space-y-2 text-sm text-text-secondary">
                <li>Complete repair scope</li>
                <li>Photo documentation</li>
                <li>Warranty-backed work</li>
              </ul>
            </div>
          </div>
        </div>
      </section>

      <CTABand
        title="Emergency Roof Repair in Overland Park"
        subtitle="Call or text now: 913-396-3717"
      />
    </>
  )
}
