import Link from 'next/link'
import { FiCheckCircle, FiDollarSign } from 'react-icons/fi'
import CTABand from '@/components/CTABand'

export const metadata = {
  title: 'Financing Options | Teamwork Roofing Kansas City',
  description: 'Flexible financing options for roofing, gutters, siding, and windows. Make your home improvement project affordable.',
}

export default function FinancingPage() {
  return (
    <>
      <section className="section-padding bg-light-bg">
        <div className="container-custom">
          <div className="text-center mb-16 max-w-3xl mx-auto">
            <FiDollarSign className="w-16 h-16 text-teamwork-blue mx-auto mb-6" />
            <h1 className="heading-1 mb-6">Teamwork Financing Options</h1>
            <p className="text-xl text-text-secondary">
              Flexible payment plans to make your roofing and exterior projects affordable
            </p>
          </div>

          <div className="grid md:grid-cols-3 gap-8 mb-16">
            <div className="card text-center">
              <h3 className="heading-4 mb-4">How It Works</h3>
              <div className="space-y-4 text-left">
                <div className="flex items-start space-x-3">
                  <div className="w-8 h-8 rounded-full bg-teamwork-blue/10 flex items-center justify-center flex-shrink-0 mt-0.5">
                    <span className="text-teamwork-blue font-bold text-sm">1</span>
                  </div>
                  <p className="text-text-secondary text-sm">Book your same-week inspection</p>
                </div>
                <div className="flex items-start space-x-3">
                  <div className="w-8 h-8 rounded-full bg-teamwork-blue/10 flex items-center justify-center flex-shrink-0 mt-0.5">
                    <span className="text-teamwork-blue font-bold text-sm">2</span>
                  </div>
                  <p className="text-text-secondary text-sm">Receive your project estimate</p>
                </div>
                <div className="flex items-start space-x-3">
                  <div className="w-8 h-8 rounded-full bg-teamwork-blue/10 flex items-center justify-center flex-shrink-0 mt-0.5">
                    <span className="text-teamwork-blue font-bold text-sm">3</span>
                  </div>
                  <p className="text-text-secondary text-sm">Review financing options with us</p>
                </div>
                <div className="flex items-start space-x-3">
                  <div className="w-8 h-8 rounded-full bg-teamwork-blue/10 flex items-center justify-center flex-shrink-0 mt-0.5">
                    <span className="text-teamwork-blue font-bold text-sm">4</span>
                  </div>
                  <p className="text-text-secondary text-sm">Choose the plan that fits your budget</p>
                </div>
              </div>
            </div>

            <div className="card bg-gradient-to-br from-teamwork-blue to-blue-700">
              <h3 className="heading-4 mb-4 text-center">What Financing Helps With</h3>
              <ul className="space-y-3">
                <li className="flex items-center space-x-2">
                  <FiCheckCircle className="w-5 h-5 text-blue-200 flex-shrink-0" />
                  <span className="text-blue-100">Roof Replacement</span>
                </li>
                <li className="flex items-center space-x-2">
                  <FiCheckCircle className="w-5 h-5 text-blue-200 flex-shrink-0" />
                  <span className="text-blue-100">Storm Damage Repairs</span>
                </li>
                <li className="flex items-center space-x-2">
                  <FiCheckCircle className="w-5 h-5 text-blue-200 flex-shrink-0" />
                  <span className="text-blue-100">Window Replacement</span>
                </li>
                <li className="flex items-center space-x-2">
                  <FiCheckCircle className="w-5 h-5 text-blue-200 flex-shrink-0" />
                  <span className="text-blue-100">Siding Installation</span>
                </li>
                <li className="flex items-center space-x-2">
                  <FiCheckCircle className="w-5 h-5 text-blue-200 flex-shrink-0" />
                  <span className="text-blue-100">Gutter Systems</span>
                </li>
                <li className="flex items-center space-x-2">
                  <FiCheckCircle className="w-5 h-5 text-blue-200 flex-shrink-0" />
                  <span className="text-blue-100">Full Exterior Upgrades</span>
                </li>
              </ul>
            </div>

            <div className="card text-center">
              <h3 className="heading-4 mb-4">Financing FAQ</h3>
              <div className="space-y-4 text-left">
                <div>
                  <p className="font-semibold text-sm mb-1">Do I need good credit?</p>
                  <p className="text-text-secondary text-sm">Multiple options available for various credit profiles</p>
                </div>
                <div>
                  <p className="font-semibold text-sm mb-1">How fast is approval?</p>
                  <p className="text-text-secondary text-sm">Often same-day or next-day decisions</p>
                </div>
                <div>
                  <p className="font-semibold text-sm mb-1">Are there fees?</p>
                  <p className="text-text-secondary text-sm">We'll explain all terms upfront — no surprises</p>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      <CTABand title="Ready to Explore Financing?" subtitle="Book your inspection and we'll review all payment options together" />
    </>
  )
}
