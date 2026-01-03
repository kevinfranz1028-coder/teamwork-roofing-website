import Link from 'next/link'
import PromiseStrip from '@/components/PromiseStrip'
import CTABand from '@/components/CTABand'
import BrandsWeInstall from '@/components/BrandsWeInstall'

export const metadata = {
  title: 'Window Replacement Kansas City | Teamwork Roofing',
  description: 'Energy-efficient window replacement in Kansas City Metro. Professional installation, multiple styles, financing available.',
}

export default function WindowsPage() {
  return (
    <>
      <section className="section-padding bg-light-bg">
        <div className="container-custom">
          <div className="max-w-3xl">
            <h1 className="heading-1 mb-6">
              Windows — <span className="text-teamwork-green">Comfort & Efficiency</span>
            </h1>
            <p className="text-xl text-text-secondary mb-8">
              Energy-efficient window replacement for comfort, lower energy bills, and improved curb appeal.
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
          <h2 className="heading-2 mb-12 text-center">Why Replace Windows</h2>
          <div className="grid md:grid-cols-3 gap-8 max-w-4xl mx-auto">
            <div className="card text-center"><h3 className="heading-4 mb-2">Lower Energy Bills</h3><p className="text-text-secondary">Modern windows reduce heating and cooling costs</p></div>
            <div className="card text-center"><h3 className="heading-4 mb-2">Increased Comfort</h3><p className="text-text-secondary">Better insulation, less drafts, quieter home</p></div>
            <div className="card text-center"><h3 className="heading-4 mb-2">Enhanced Value</h3><p className="text-text-secondary">Improve curb appeal and home value</p></div>
          </div>
        </div>
      </section>

      {/* Brands We Install */}
      <BrandsWeInstall variant="compact" />

      <CTABand />
    </>
  )
}
