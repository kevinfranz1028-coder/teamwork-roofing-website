import { FiShield, FiCheckCircle, FiX } from 'react-icons/fi'
import CTABand from '@/components/CTABand'

export const metadata = {
  title: 'Teamwork Warranty | Roofing Services Kansas City',
  description: 'Our warranty commitment: professional installation backed by the Teamwork partnership promise.',
}

export default function WarrantyPage() {
  return (
    <>
      <section className="section-padding bg-light-bg">
        <div className="container-custom">
          <div className="text-center mb-16 max-w-3xl mx-auto">
            <FiShield className="w-16 h-16 text-teamwork-blue mx-auto mb-6" />
            <h1 className="heading-1 mb-6">The Teamwork Warranty</h1>
            <p className="text-xl text-text-secondary">
              Our installation work is backed by our partnership commitment — we stand behind every project
            </p>
          </div>

          <div className="max-w-4xl mx-auto space-y-12">
            <div className="group card hover:border-teamwork-blue transition-all duration-300 hover:shadow-xl hover:-translate-y-1">
              <h2 className="heading-3 mb-6 group-hover:text-teamwork-blue transition-colors">What's Covered</h2>
              <div className="space-y-4">
                <div className="flex items-start space-x-3 group/item hover:translate-x-1 transition-transform duration-200">
                  <FiCheckCircle className="w-6 h-6 text-teamwork-blue mt-1 flex-shrink-0 group-hover/item:scale-110 transition-transform" />
                  <div>
                    <h4 className="font-semibold mb-1 group-hover/item:text-teamwork-blue transition-colors">Installation Workmanship</h4>
                    <p className="text-text-secondary text-sm">Our installation labor and methods are warranted against defects</p>
                  </div>
                </div>
                <div className="flex items-start space-x-3 group/item hover:translate-x-1 transition-transform duration-200">
                  <FiCheckCircle className="w-6 h-6 text-teamwork-blue mt-1 flex-shrink-0 group-hover/item:scale-110 transition-transform" />
                  <div>
                    <h4 className="font-semibold mb-1 group-hover/item:text-teamwork-blue transition-colors">Material Defects</h4>
                    <p className="text-text-secondary text-sm">Manufacturer warranties honored (varies by product: 25 years to lifetime)</p>
                  </div>
                </div>
                <div className="flex items-start space-x-3 group/item hover:translate-x-1 transition-transform duration-200">
                  <FiCheckCircle className="w-6 h-6 text-teamwork-blue mt-1 flex-shrink-0 group-hover/item:scale-110 transition-transform" />
                  <div>
                    <h4 className="font-semibold mb-1 group-hover/item:text-teamwork-blue transition-colors">Leak-Free Performance</h4>
                    <p className="text-text-secondary text-sm">Proper installation to prevent leaks from workmanship issues</p>
                  </div>
                </div>
                <div className="flex items-start space-x-3 group/item hover:translate-x-1 transition-transform duration-200">
                  <FiCheckCircle className="w-6 h-6 text-teamwork-blue mt-1 flex-shrink-0 group-hover/item:scale-110 transition-transform" />
                  <div>
                    <h4 className="font-semibold mb-1 group-hover/item:text-teamwork-blue transition-colors">Clean Site Performance</h4>
                    <p className="text-text-secondary text-sm">Property protection during and after installation</p>
                  </div>
                </div>
              </div>
            </div>

            <div className="group card hover:border-red-500/30 transition-all duration-300 hover:shadow-xl hover:-translate-y-1">
              <h2 className="heading-3 mb-6 group-hover:text-red-600 transition-colors">What's Not Covered</h2>
              <div className="space-y-4">
                <div className="flex items-start space-x-3 group/item hover:translate-x-1 transition-transform duration-200">
                  <FiX className="w-6 h-6 text-red-500 mt-1 flex-shrink-0 group-hover/item:scale-110 transition-transform" />
                  <div>
                    <h4 className="font-semibold mb-1 group-hover/item:text-red-600 transition-colors">Storm or Weather Damage</h4>
                    <p className="text-text-secondary text-sm">Acts of nature (hail, wind, ice dams, etc.) are not covered</p>
                  </div>
                </div>
                <div className="flex items-start space-x-3 group/item hover:translate-x-1 transition-transform duration-200">
                  <FiX className="w-6 h-6 text-red-500 mt-1 flex-shrink-0 group-hover/item:scale-110 transition-transform" />
                  <div>
                    <h4 className="font-semibold mb-1 group-hover/item:text-red-600 transition-colors">Neglect or Lack of Maintenance</h4>
                    <p className="text-text-secondary text-sm">Failure to maintain gutters, roof debris removal, etc.</p>
                  </div>
                </div>
                <div className="flex items-start space-x-3 group/item hover:translate-x-1 transition-transform duration-200">
                  <FiX className="w-6 h-6 text-red-500 mt-1 flex-shrink-0 group-hover/item:scale-110 transition-transform" />
                  <div>
                    <h4 className="font-semibold mb-1 group-hover/item:text-red-600 transition-colors">Modifications by Others</h4>
                    <p className="text-text-secondary text-sm">Work performed by other contractors after our installation</p>
                  </div>
                </div>
                <div className="flex items-start space-x-3 group/item hover:translate-x-1 transition-transform duration-200">
                  <FiX className="w-6 h-6 text-red-500 mt-1 flex-shrink-0 group-hover/item:scale-110 transition-transform" />
                  <div>
                    <h4 className="font-semibold mb-1 group-hover/item:text-red-600 transition-colors">Normal Wear and Tear</h4>
                    <p className="text-text-secondary text-sm">Expected aging beyond material warranty period</p>
                  </div>
                </div>
              </div>
            </div>

            <div className="group card bg-white hover:border-teamwork-blue transition-all duration-300 hover:shadow-xl hover:-translate-y-1">
              <h2 className="heading-3 mb-6 group-hover:text-teamwork-blue transition-colors">How to Request Warranty Support</h2>
              <div className="space-y-4">
                <p className="text-text-secondary">If you experience an issue you believe is covered under warranty:</p>
                <ol className="space-y-3">
                  <li className="flex items-start space-x-3 group/item hover:translate-x-1 transition-transform duration-200">
                    <span className="font-bold text-teamwork-blue group-hover/item:scale-110 transition-transform">1.</span>
                    <span className="text-text-secondary">Call us at <a href="tel:9133963717" className="text-teamwork-blue hover:underline">913-396-3717</a> or use our contact form</span>
                  </li>
                  <li className="flex items-start space-x-3 group/item hover:translate-x-1 transition-transform duration-200">
                    <span className="font-bold text-teamwork-blue group-hover/item:scale-110 transition-transform">2.</span>
                    <span className="text-text-secondary">Describe the issue and provide photos if possible</span>
                  </li>
                  <li className="flex items-start space-x-3 group/item hover:translate-x-1 transition-transform duration-200">
                    <span className="font-bold text-teamwork-blue group-hover/item:scale-110 transition-transform">3.</span>
                    <span className="text-text-secondary">We'll schedule an inspection to assess the claim</span>
                  </li>
                  <li className="flex items-start space-x-3 group/item hover:translate-x-1 transition-transform duration-200">
                    <span className="font-bold text-teamwork-blue group-hover/item:scale-110 transition-transform">4.</span>
                    <span className="text-text-secondary">If covered, we'll repair or replace at no cost to you</span>
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
