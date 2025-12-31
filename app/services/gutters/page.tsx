import Link from 'next/link'
import { FiCheckCircle } from 'react-icons/fi'
import PromiseStrip from '@/components/PromiseStrip'
import CTABand from '@/components/CTABand'
import BrandsWeInstall from '@/components/BrandsWeInstall'

export const metadata = {
  title: 'Gutter Installation & Repair Kansas City | Teamwork Roofing',
  description: 'Seamless gutters, gutter guards, and professional repair in Kansas City Metro. Photo-documented, clean site guarantee.',
}

export default function GuttersPage() {
  return (
    <>
      <section className="section-padding bg-dark-bg">
        <div className="container-custom">
          <div className="max-w-3xl">
            <h1 className="heading-1 mb-6">
              Gutters — <span className="text-teamwork-blue">Seamless, Guards, Repair</span>
            </h1>
            <p className="text-xl text-gray-400 mb-8">
              Protect your home with professional gutter services. Seamless installation, guard options, and expert repairs.
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
          <h2 className="heading-2 mb-12 text-center">Our Gutter Services</h2>
          <div className="grid md:grid-cols-3 gap-8">
            <div className="card">
              <h3 className="heading-4 mb-3">Seamless Installation</h3>
              <p className="text-gray-400 mb-4">Custom-fit gutters with no leaky seams. Multiple colors available.</p>
              <ul className="space-y-2 text-sm text-gray-500">
                <li className="flex items-center"><FiCheckCircle className="w-4 h-4 text-teamwork-blue mr-2" />5" & 6" sizes</li>
                <li className="flex items-center"><FiCheckCircle className="w-4 h-4 text-teamwork-blue mr-2" />Color matching</li>
                <li className="flex items-center"><FiCheckCircle className="w-4 h-4 text-teamwork-blue mr-2" />Proper pitch</li>
              </ul>
            </div>

            <div className="card">
              <h3 className="heading-4 mb-3">Gutter Guards</h3>
              <p className="text-gray-400 mb-4">Keep debris out, reduce maintenance, protect your investment.</p>
              <ul className="space-y-2 text-sm text-gray-500">
                <li className="flex items-center"><FiCheckCircle className="w-4 h-4 text-teamwork-blue mr-2" />Mesh guards</li>
                <li className="flex items-center"><FiCheckCircle className="w-4 h-4 text-teamwork-blue mr-2" />Screen options</li>
                <li className="flex items-center"><FiCheckCircle className="w-4 h-4 text-teamwork-blue mr-2" />Easy maintenance</li>
              </ul>
            </div>

            <div className="card">
              <h3 className="heading-4 mb-3">Repair</h3>
              <p className="text-gray-400 mb-4">Fix sagging, leaks, and damage fast with our same-week service.</p>
              <ul className="space-y-2 text-sm text-gray-500">
                <li className="flex items-center"><FiCheckCircle className="w-4 h-4 text-teamwork-blue mr-2" />Leak sealing</li>
                <li className="flex items-center"><FiCheckCircle className="w-4 h-4 text-teamwork-blue mr-2" />Re-hanging</li>
                <li className="flex items-center"><FiCheckCircle className="w-4 h-4 text-teamwork-blue mr-2" />Downspout fixes</li>
              </ul>
            </div>
          </div>
        </div>
      </section>

      <section className="section-padding bg-dark-bg">
        <div className="container-custom">
          <h2 className="heading-2 mb-12 text-center">Signs of Failing Gutters</h2>
          <div className="grid md:grid-cols-2 gap-4 max-w-3xl mx-auto">
            {['Water pooling near foundation', 'Sagging or pulling away', 'Overflow during rain', 'Rust or holes', 'Peeling paint on gutters', 'Basement water issues'].map((sign, index) => (
              <div key={index} className="flex items-start space-x-3">
                <FiCheckCircle className="w-5 h-5 text-teamwork-blue mt-1 flex-shrink-0" />
                <span className="text-gray-300">{sign}</span>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Brands We Install */}
      <BrandsWeInstall variant="compact" />

      <CTABand title="Ready for Better Gutters?" />
    </>
  )
}
