import { FiShield, FiCheckCircle, FiX } from 'react-icons/fi'
import CTABand from '@/components/CTABand'

export const metadata = {
  title: 'Teamwork Warranty | Roofing Services Kansas City',
  description: 'Our warranty commitment: professional installation backed by the Teamwork partnership promise.',
}

export default function WarrantyPage() {
  return (
    <>
      <section className="section-padding bg-dark-bg">
        <div className="container-custom">
          <div className="text-center mb-16 max-w-3xl mx-auto">
            <FiShield className="w-16 h-16 text-teamwork-blue mx-auto mb-6" />
            <h1 className="heading-1 mb-6">The Teamwork Warranty</h1>
            <p className="text-xl text-gray-400">
              Our installation work is backed by our partnership commitment — we stand behind every project
            </p>
          </div>

          <div className="max-w-4xl mx-auto space-y-12">
            <div className="card">
              <h2 className="heading-3 mb-6">What's Covered</h2>
              <div className="space-y-4">
                <div className="flex items-start space-x-3">
                  <FiCheckCircle className="w-6 h-6 text-teamwork-blue mt-1 flex-shrink-0" />
                  <div>
                    <h4 className="font-semibold mb-1">Installation Workmanship</h4>
                    <p className="text-gray-400 text-sm">Our installation labor and methods are warranted against defects</p>
                  </div>
                </div>
                <div className="flex items-start space-x-3">
                  <FiCheckCircle className="w-6 h-6 text-teamwork-blue mt-1 flex-shrink-0" />
                  <div>
                    <h4 className="font-semibold mb-1">Material Defects</h4>
                    <p className="text-gray-400 text-sm">Manufacturer warranties honored (varies by product: 25 years to lifetime)</p>
                  </div>
                </div>
                <div className="flex items-start space-x-3">
                  <FiCheckCircle className="w-6 h-6 text-teamwork-blue mt-1 flex-shrink-0" />
                  <div>
                    <h4 className="font-semibold mb-1">Leak-Free Performance</h4>
                    <p className="text-gray-400 text-sm">Proper installation to prevent leaks from workmanship issues</p>
                  </div>
                </div>
                <div className="flex items-start space-x-3">
                  <FiCheckCircle className="w-6 h-6 text-teamwork-blue mt-1 flex-shrink-0" />
                  <div>
                    <h4 className="font-semibold mb-1">Clean Site Performance</h4>
                    <p className="text-gray-400 text-sm">Property protection during and after installation</p>
                  </div>
                </div>
              </div>
            </div>

            <div className="card">
              <h2 className="heading-3 mb-6">What's Not Covered</h2>
              <div className="space-y-4">
                <div className="flex items-start space-x-3">
                  <FiX className="w-6 h-6 text-red-500 mt-1 flex-shrink-0" />
                  <div>
                    <h4 className="font-semibold mb-1">Storm or Weather Damage</h4>
                    <p className="text-gray-400 text-sm">Acts of nature (hail, wind, ice dams, etc.) are not covered</p>
                  </div>
                </div>
                <div className="flex items-start space-x-3">
                  <FiX className="w-6 h-6 text-red-500 mt-1 flex-shrink-0" />
                  <div>
                    <h4 className="font-semibold mb-1">Neglect or Lack of Maintenance</h4>
                    <p className="text-gray-400 text-sm">Failure to maintain gutters, roof debris removal, etc.</p>
                  </div>
                </div>
                <div className="flex items-start space-x-3">
                  <FiX className="w-6 h-6 text-red-500 mt-1 flex-shrink-0" />
                  <div>
                    <h4 className="font-semibold mb-1">Modifications by Others</h4>
                    <p className="text-gray-400 text-sm">Work performed by other contractors after our installation</p>
                  </div>
                </div>
                <div className="flex items-start space-x-3">
                  <FiX className="w-6 h-6 text-red-500 mt-1 flex-shrink-0" />
                  <div>
                    <h4 className="font-semibold mb-1">Normal Wear and Tear</h4>
                    <p className="text-gray-400 text-sm">Expected aging beyond material warranty period</p>
                  </div>
                </div>
              </div>
            </div>

            <div className="card bg-dark-surface">
              <h2 className="heading-3 mb-6">How to Request Warranty Support</h2>
              <div className="space-y-4">
                <p className="text-gray-400">If you experience an issue you believe is covered under warranty:</p>
                <ol className="space-y-3">
                  <li className="flex items-start space-x-3">
                    <span className="font-bold text-teamwork-blue">1.</span>
                    <span className="text-gray-300">Call us at <a href="tel:9133963717" className="text-teamwork-blue hover:underline">913-396-3717</a> or use our contact form</span>
                  </li>
                  <li className="flex items-start space-x-3">
                    <span className="font-bold text-teamwork-blue">2.</span>
                    <span className="text-gray-300">Describe the issue and provide photos if possible</span>
                  </li>
                  <li className="flex items-start space-x-3">
                    <span className="font-bold text-teamwork-blue">3.</span>
                    <span className="text-gray-300">We'll schedule an inspection to assess the claim</span>
                  </li>
                  <li className="flex items-start space-x-3">
                    <span className="font-bold text-teamwork-blue">4.</span>
                    <span className="text-gray-300">If covered, we'll repair or replace at no cost to you</span>
                  </li>
                </ol>
              </div>
            </div>
          </div>
        </div>
      </section>

      <CTABand title="Questions About Our Warranty?" subtitle="Contact us anytime — we're here to help" />
    </>
  )
}
