import Link from 'next/link'
import { FiPhone, FiMessageSquare, FiCheckCircle, FiAlertCircle } from 'react-icons/fi'
import PromiseStrip from '@/components/PromiseStrip'
import CTABand from '@/components/CTABand'
import { cities } from '@/content/cities'

export const metadata = {
  title: 'Emergency Roof Repair Leawood | Call/Text Now | Teamwork',
  description: 'Emergency roof repair in Leawood, KS. Active leaks, storm damage, urgent repairs. Same-day response. Call or text 913-396-3717 now.',
}

const cityData = cities['leawood-ks']

export default function EmergencyRoofRepairPage() {
  return (
    <>
      <div className="bg-white border-b border-light-border">
        <div className="container-custom py-4">
          <div className="flex items-center space-x-2 text-sm text-text-muted">
            <Link href="/" className="hover:text-teamwork-blue">Home</Link>
            <span>/</span>
            <Link href={`/${cityData.slug}/`} className="hover:text-teamwork-blue">{cityData.cityName}</Link>
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
            <h1 className="heading-1 mb-6">Emergency Roof Repair in {cityData.cityName}</h1>
            <p className="text-xl text-text-secondary mb-8">
              Active leak? Storm damage? We respond fast in {cityData.cityName}. Call or text now for same-day emergency service.
            </p>

            <div className="flex flex-col sm:flex-row gap-4 justify-center mb-8">
              <a href={`tel:${cityData.phone}`} className="btn-primary text-lg">
                <FiPhone className="inline mr-2" />
                Call Now: {cityData.phone}
              </a>
              <a href={`sms:${cityData.phone}`} className="btn-primary bg-green-600 hover:bg-green-700 text-lg">
                <FiMessageSquare className="inline mr-2" />
                Text: {cityData.phone}
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
                <span className="text-text-secondary">Call or text us immediately: {cityData.phone}</span>
              </li>
            </ol>
            <p className="text-text-secondary text-sm text-center mt-6">
              Need non-emergency help? <Link href={`/${cityData.slug}/roof-repair/`} className="text-teamwork-blue hover:underline">See Roof Repair in {cityData.cityName} →</Link>
            </p>
          </div>
        </div>
      </section>

      <section className="section-padding bg-light-bg">
        <div className="container-custom">
          <h2 className="heading-2 mb-12 text-center">Text Us Photos</h2>
          <div className="max-w-3xl mx-auto">
            <p className="text-text-secondary mb-6 text-center">Text photos to {cityData.phone}. Include:</p>
            <div className="grid md:grid-cols-2 gap-6">
              <div className="card">
                <h4 className="font-semibold mb-3">Interior Photos</h4>
                <ul className="space-y-2 text-sm text-text-secondary">
                  <li className="flex items-start"><FiCheckCircle className="w-4 h-4 text-teamwork-blue mt-0.5 mr-2 flex-shrink-0" />Ceiling stains or drips</li>
                  <li className="flex items-start"><FiCheckCircle className="w-4 h-4 text-teamwork-blue mt-0.5 mr-2 flex-shrink-0" />Water pooling on floor</li>
                  <li className="flex items-start"><FiCheckCircle className="w-4 h-4 text-teamwork-blue mt-0.5 mr-2 flex-shrink-0" />Wet walls or insulation</li>
                </ul>
              </div>
              <div className="card">
                <h4 className="font-semibold mb-3">Exterior Photos (if safe)</h4>
                <ul className="space-y-2 text-sm text-text-secondary">
                  <li className="flex items-start"><FiCheckCircle className="w-4 h-4 text-teamwork-blue mt-0.5 mr-2 flex-shrink-0" />Missing shingles</li>
                  <li className="flex items-start"><FiCheckCircle className="w-4 h-4 text-teamwork-blue mt-0.5 mr-2 flex-shrink-0" />Visible damage from ground</li>
                  <li className="flex items-start"><FiCheckCircle className="w-4 h-4 text-teamwork-blue mt-0.5 mr-2 flex-shrink-0" />Debris or tree damage</li>
                </ul>
              </div>
            </div>
            <p className="text-xs text-text-muted text-center mt-6">Do not climb on roof if conditions are unsafe. We will inspect safely when we arrive.</p>
          </div>
        </div>
      </section>

      <section className="section-padding bg-white">
        <div className="container-custom">
          <h2 className="heading-2 mb-12 text-center">What Happens Next</h2>
          <div className="max-w-3xl mx-auto space-y-4">
            <div className="card">
              <h4 className="font-semibold mb-2">1. We respond same-day</h4>
              <p className="text-text-secondary text-sm">Call or text received - we will contact you back within hours (often minutes)</p>
            </div>
            <div className="card">
              <h4 className="font-semibold mb-2">2. Urgent inspection scheduled</h4>
              <p className="text-text-secondary text-sm">We schedule your inspection as fast as possible - often same day or next day</p>
            </div>
            <div className="card">
              <h4 className="font-semibold mb-2">3. Temporary mitigation if needed</h4>
              <p className="text-text-secondary text-sm">If immediate action is needed to prevent further damage, we will provide temporary protection</p>
            </div>
            <div className="card">
              <h4 className="font-semibold mb-2">4. Photo documentation & repair plan</h4>
              <p className="text-text-secondary text-sm">Full inspection with photos, clear scope, honest pricing</p>
            </div>
            <div className="card">
              <h4 className="font-semibold mb-2">5. Permanent repair scheduled</h4>
              <p className="text-text-secondary text-sm">Professional repair with clean site practices and warranty backing</p>
            </div>
          </div>
        </div>
      </section>

      <CTABand title="Need Emergency Help Now?" subtitle={`Call or text ${cityData.phone} — we respond same-day`} />
    </>
  )
}
