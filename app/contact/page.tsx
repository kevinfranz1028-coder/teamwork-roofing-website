'use client'

import { useState } from 'react'
import { FiPhone, FiMail, FiMapPin, FiCheckCircle } from 'react-icons/fi'
import PromiseStrip from '@/components/PromiseStrip'

export default function ContactPage() {
  const [formData, setFormData] = useState({
    name: '',
    phone: '',
    email: '',
    service: '',
    message: ''
  })
  const [submitted, setSubmitted] = useState(false)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    console.log('Contact form submitted:', formData)
    setSubmitted(true)
    setTimeout(() => {
      setSubmitted(false)
      setFormData({ name: '', phone: '', email: '', service: '', message: '' })
    }, 3000)
  }

  if (submitted) {
    return (
      <section className="section-padding bg-light-bg min-h-screen flex items-center justify-center">
        <div className="card max-w-2xl text-center">
          <div className="w-20 h-20 rounded-full bg-green-500/10 flex items-center justify-center mx-auto mb-6">
            <FiCheckCircle className="w-10 h-10 text-green-500" />
          </div>
          <h1 className="heading-2 mb-4">Message Sent!</h1>
          <p className="text-xl text-text-secondary">
            Thank you for contacting Teamwork Roofing. We'll respond within 24 hours.
          </p>
        </div>
      </section>
    )
  }

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
              <div className="card bg-gradient-to-br from-teamwork-blue to-blue-700">
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
                      <p className="text-blue-100">913-396-3717</p>
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
                      <p className="text-blue-100">913-396-3717</p>
                    </div>
                  </a>
                </div>
              </div>

              <div className="card">
                <h3 className="heading-4 mb-4">Service Area</h3>
                <div className="flex items-start space-x-3 mb-4">
                  <FiMapPin className="w-5 h-5 text-teamwork-blue mt-1 flex-shrink-0" />
                  <div>
                    <p className="text-text-secondary mb-2">Kansas City Metro</p>
                    <p className="text-sm text-text-muted">
                      KCK, KCMO, Johnson County, Wyandotte County, Jackson County, and nearby areas in Kansas and Missouri
                    </p>
                  </div>
                </div>
              </div>

              <div className="card bg-white">
                <h3 className="heading-4 mb-4">What to Expect</h3>
                <ul className="space-y-3 text-sm text-text-secondary">
                  <li className="flex items-start space-x-2">
                    <FiCheckCircle className="w-5 h-5 text-teamwork-blue mt-0.5 flex-shrink-0" />
                    <span>Response within 24 hours</span>
                  </li>
                  <li className="flex items-start space-x-2">
                    <FiCheckCircle className="w-5 h-5 text-teamwork-blue mt-0.5 flex-shrink-0" />
                    <span>Same-week inspection available</span>
                  </li>
                  <li className="flex items-start space-x-2">
                    <FiCheckCircle className="w-5 h-5 text-teamwork-blue mt-0.5 flex-shrink-0" />
                    <span>No pressure, clear communication</span>
                  </li>
                </ul>
              </div>
            </div>

            {/* Contact Form */}
            <div className="card">
              <h3 className="heading-4 mb-6">Send Us a Message</h3>
              <form onSubmit={handleSubmit} className="space-y-4">
                <div>
                  <label className="block text-sm font-semibold mb-2">
                    Name <span className="text-red-500">*</span>
                  </label>
                  <input
                    type="text"
                    value={formData.name}
                    onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                    className="w-full px-4 py-3 bg-light-bg border border-light-border rounded-lg focus:border-teamwork-blue focus:outline-none"
                    required
                  />
                </div>

                <div>
                  <label className="block text-sm font-semibold mb-2">
                    Phone <span className="text-red-500">*</span>
                  </label>
                  <input
                    type="tel"
                    value={formData.phone}
                    onChange={(e) => setFormData({ ...formData, phone: e.target.value })}
                    className="w-full px-4 py-3 bg-light-bg border border-light-border rounded-lg focus:border-teamwork-blue focus:outline-none"
                    required
                  />
                </div>

                <div>
                  <label className="block text-sm font-semibold mb-2">Email</label>
                  <input
                    type="email"
                    value={formData.email}
                    onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                    className="w-full px-4 py-3 bg-light-bg border border-light-border rounded-lg focus:border-teamwork-blue focus:outline-none"
                  />
                </div>

                <div>
                  <label className="block text-sm font-semibold mb-2">Service Interested In</label>
                  <select
                    value={formData.service}
                    onChange={(e) => setFormData({ ...formData, service: e.target.value })}
                    className="w-full px-4 py-3 bg-light-bg border border-light-border rounded-lg focus:border-teamwork-blue focus:outline-none"
                  >
                    <option value="">Select a service</option>
                    <option value="roof-replacement">Roof Replacement</option>
                    <option value="roof-repair">Roof Repair</option>
                    <option value="storm-damage">Storm Damage</option>
                    <option value="gutters">Gutters</option>
                    <option value="siding">Siding</option>
                    <option value="windows">Windows</option>
                    <option value="not-sure">Not Sure</option>
                  </select>
                </div>

                <div>
                  <label className="block text-sm font-semibold mb-2">
                    Message <span className="text-red-500">*</span>
                  </label>
                  <textarea
                    value={formData.message}
                    onChange={(e) => setFormData({ ...formData, message: e.target.value })}
                    rows={5}
                    className="w-full px-4 py-3 bg-light-bg border border-light-border rounded-lg focus:border-teamwork-blue focus:outline-none"
                    required
                  />
                </div>

                <button type="submit" className="btn-primary w-full">
                  Send Message
                </button>

                <p className="text-xs text-text-muted text-center">
                  By submitting, you agree to receive calls/texts from Teamwork Roofing Services.
                </p>
              </form>
            </div>
          </div>
        </div>
      </section>

      <PromiseStrip />
    </>
  )
}
