'use client'

import { FiPhone, FiMail, FiMapPin, FiCheckCircle } from 'react-icons/fi'
import PromiseStrip from '@/components/PromiseStrip'
import ContactForm from '@/components/forms/ContactForm'

export default function ContactPage() {

  return (
    <>
      <section className="section-padding bg-light-bg">
        <div className="container-custom">
          <div className="text-center mb-12">
            <h1 className="heading-1 mb-6">Contact Us</h1>
            <p className="text-xl text-text-secondary">
              Call, text, or send us a message — we're here to help
            </p>
          </div>

          <div className="grid lg:grid-cols-2 gap-12 max-w-5xl mx-auto">
            {/* Contact Methods */}
            <div className="space-y-8">
              <div className="card bg-gradient-to-br from-teamwork-green to-green-700">
                <h3 className="heading-4 mb-6">Fastest Response</h3>
                <div className="space-y-4">
                  <a
                    href="tel:9133963717"
                    className="flex items-center space-x-4 p-4 bg-white/10 rounded-lg hover:bg-white/20 transition-colors"
                  >
                    <div className="w-12 h-12 rounded-full bg-white/20 flex items-center justify-center">
                      <FiPhone className="w-6 h-6" />
                    </div>
                    <div>
                      <p className="font-semibold">Call Us</p>
                      <p className="text-green-100">913-396-3717</p>
                    </div>
                  </a>

                  <a
                    href="sms:9133963717"
                    className="flex items-center space-x-4 p-4 bg-white/10 rounded-lg hover:bg-white/20 transition-colors"
                  >
                    <div className="w-12 h-12 rounded-full bg-white/20 flex items-center justify-center">
                      <FiMail className="w-6 h-6" />
                    </div>
                    <div>
                      <p className="font-semibold">Text Us</p>
                      <p className="text-green-100">913-396-3717</p>
                    </div>
                  </a>
                </div>
              </div>

              <div className="group card hover:border-teamwork-green transition-all duration-300 hover:shadow-lg hover:-translate-y-0.5">
                <h3 className="heading-4 mb-4 group-hover:text-teamwork-green transition-colors">Service Area</h3>
                <div className="flex items-start space-x-3 mb-4">
                  <FiMapPin className="w-5 h-5 text-teamwork-green mt-1 flex-shrink-0" />
                  <div>
                    <p className="text-text-secondary mb-2">Kansas City Metro</p>
                    <p className="text-sm text-text-muted">
                      KCK, KCMO, Johnson County, Wyandotte County, Jackson County, and nearby areas in Kansas and Missouri
                    </p>
                  </div>
                </div>
              </div>

              <div className="group card bg-white hover:border-teamwork-green transition-all duration-300 hover:shadow-lg hover:-translate-y-0.5">
                <h3 className="heading-4 mb-4 group-hover:text-teamwork-green transition-colors">What to Expect</h3>
                <ul className="space-y-3 text-sm text-text-secondary">
                  <li className="flex items-start space-x-2 group/item hover:translate-x-1 transition-transform duration-200">
                    <FiCheckCircle className="w-5 h-5 text-teamwork-green mt-0.5 flex-shrink-0" />
                    <span>Response within 24 hours</span>
                  </li>
                  <li className="flex items-start space-x-2 group/item hover:translate-x-1 transition-transform duration-200">
                    <FiCheckCircle className="w-5 h-5 text-teamwork-green mt-0.5 flex-shrink-0" />
                    <span>Same-week inspection available</span>
                  </li>
                  <li className="flex items-start space-x-2 group/item hover:translate-x-1 transition-transform duration-200">
                    <FiCheckCircle className="w-5 h-5 text-teamwork-green mt-0.5 flex-shrink-0" />
                    <span>No pressure, clear communication</span>
                  </li>
                </ul>
              </div>
            </div>

            {/* Contact Form */}
            <ContactForm />
          </div>
        </div>
      </section>

      <PromiseStrip />
    </>
  )
}
