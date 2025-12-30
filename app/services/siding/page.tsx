import Link from 'next/link'
import PromiseStrip from '@/components/PromiseStrip'
import CTABand from '@/components/CTABand'

export const metadata = {
  title: 'Siding Installation & Repair Kansas City | Teamwork Roofing',
  description: 'Professional siding installation and repair in Kansas City Metro. Multiple material options, expert installation.',
}

export default function SidingPage() {
  return (
    <>
      <section className="section-padding bg-dark-bg">
        <div className="container-custom">
          <div className="max-w-3xl">
            <h1 className="heading-1 mb-6">
              Siding — <span className="text-teamwork-blue">Protect & Beautify</span>
            </h1>
            <p className="text-xl text-gray-400 mb-8">
              Transform your home's exterior with professional siding installation or repair. Multiple materials, expert craftsmanship.
            </p>
            <div className="flex flex-wrap gap-4">
              <Link href="/book/" className="btn-primary">Book Inspection</Link>
              <Link href="/estimate/" className="btn-secondary">Get Estimate</Link>
            </div>
          </div>
        </div>
      </section>

      <PromiseStrip />

      <section className="section-padding bg-dark-surface">
        <div className="container-custom">
          <h2 className="heading-2 mb-12 text-center">Siding Materials</h2>
          <div className="grid md:grid-cols-3 gap-8">
            <div className="card"><h3 className="heading-4 mb-2">Vinyl</h3><p className="text-gray-400">Low maintenance, affordable, wide color selection</p></div>
            <div className="card"><h3 className="heading-4 mb-2">Fiber Cement</h3><p className="text-gray-400">Durable, fire-resistant, premium appearance</p></div>
            <div className="card"><h3 className="heading-4 mb-2">Wood & Composite</h3><p className="text-gray-400">Natural beauty, classic appeal</p></div>
          </div>
        </div>
      </section>

      <CTABand />
    </>
  )
}
