'use client'

import { useState } from 'react'
import { FiCalendar, FiClock, FiMapPin, FiPhone, FiMail, FiUser, FiCheckCircle } from 'react-icons/fi'
import PromiseStrip from '@/components/PromiseStrip'

export default function BookPage() {
  const [formData, setFormData] = useState({
    name: '',
    phone: '',
    email: '',
    address: '',
    city: '',
    urgency: '',
    preferredDate: '',
    preferredTime: '',
    service: '',
    notes: ''
  })
  const [submitted, setSubmitted] = useState(false)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()

    // Here you would send the booking to your API
    console.log('Booking submitted:', formData)

    setSubmitted(true)

    // Reset after showing success
    setTimeout(() => {
      setSubmitted(false)
      setFormData({
        name: '',
        phone: '',
        email: '',
        address: '',
        city: '',
        urgency: '',
        preferredDate: '',
        preferredTime: '',
        service: '',
        notes: ''
      })
    }, 3000)
  }

  if (submitted) {
    return (
      <section className="section-padding bg-dark-bg min-h-screen flex items-center justify-center">
        <div className="card max-w-2xl text-center">
          <div className="w-20 h-20 rounded-full bg-green-500/10 flex items-center justify-center mx-auto mb-6">
            <FiCheckCircle className="w-10 h-10 text-green-500" />
          </div>
          <h1 className="heading-2 mb-4">Inspection Requested!</h1>
          <p className="text-xl text-gray-400 mb-6">
            Thank you for choosing Teamwork Roofing. We'll contact you within 24 hours to confirm your same-week inspection.
          </p>
          <p className="text-gray-500">
            Questions? Call us at <a href="tel:9133963717" className="text-teamwork-blue hover:underline">913-396-3717</a>
          </p>
        </div>
      </section>
    )
  }

  return (
    <>
      <section className="section-padding bg-dark-bg">
        <div className="container-custom max-w-4xl">
          {/* Header */}
          <div className="text-center mb-12">
            <h1 className="heading-1 mb-4">Book Your Same-Week Inspection</h1>
            <p className="text-xl text-gray-400 mb-6">
              Fast, professional, photo-documented — we'll schedule within the same week
            </p>
            <div className="inline-flex items-center space-x-2 bg-teamwork-blue/10 border border-teamwork-blue px-4 py-2 rounded-lg">
              <FiClock className="w-5 h-5 text-teamwork-blue" />
              <span className="text-teamwork-blue font-semibold">Same-Week Promise</span>
            </div>
          </div>

          <div className="grid lg:grid-cols-3 gap-8">
            {/* Form */}
            <div className="lg:col-span-2">
              <form onSubmit={handleSubmit} className="card space-y-6">
                <h2 className="heading-4 mb-6">Inspection Request Form</h2>

                {/* Contact Info */}
                <div className="grid md:grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-semibold mb-2">
                      <FiUser className="inline w-4 h-4 mr-2" />
                      Name <span className="text-red-500">*</span>
                    </label>
                    <input
                      type="text"
                      value={formData.name}
                      onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                      className="w-full px-4 py-3 bg-dark-bg border border-dark-border rounded-lg focus:border-teamwork-blue focus:outline-none"
                      required
                    />
                  </div>

                  <div>
                    <label className="block text-sm font-semibold mb-2">
                      <FiPhone className="inline w-4 h-4 mr-2" />
                      Phone <span className="text-red-500">*</span>
                    </label>
                    <input
                      type="tel"
                      value={formData.phone}
                      onChange={(e) => setFormData({ ...formData, phone: e.target.value })}
                      className="w-full px-4 py-3 bg-dark-bg border border-dark-border rounded-lg focus:border-teamwork-blue focus:outline-none"
                      required
                    />
                  </div>
                </div>

                <div>
                  <label className="block text-sm font-semibold mb-2">
                    <FiMail className="inline w-4 h-4 mr-2" />
                    Email
                  </label>
                  <input
                    type="email"
                    value={formData.email}
                    onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                    className="w-full px-4 py-3 bg-dark-bg border border-dark-border rounded-lg focus:border-teamwork-blue focus:outline-none"
                  />
                </div>

                {/* Address */}
                <div className="grid md:grid-cols-3 gap-4">
                  <div className="md:col-span-2">
                    <label className="block text-sm font-semibold mb-2">
                      <FiMapPin className="inline w-4 h-4 mr-2" />
                      Street Address <span className="text-red-500">*</span>
                    </label>
                    <input
                      type="text"
                      value={formData.address}
                      onChange={(e) => setFormData({ ...formData, address: e.target.value })}
                      className="w-full px-4 py-3 bg-dark-bg border border-dark-border rounded-lg focus:border-teamwork-blue focus:outline-none"
                      required
                    />
                  </div>

                  <div>
                    <label className="block text-sm font-semibold mb-2">City</label>
                    <input
                      type="text"
                      value={formData.city}
                      onChange={(e) => setFormData({ ...formData, city: e.target.value })}
                      className="w-full px-4 py-3 bg-dark-bg border border-dark-border rounded-lg focus:border-teamwork-blue focus:outline-none"
                    />
                  </div>
                </div>

                {/* Service & Urgency */}
                <div className="grid md:grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-semibold mb-2">
                      Service Needed <span className="text-red-500">*</span>
                    </label>
                    <select
                      value={formData.service}
                      onChange={(e) => setFormData({ ...formData, service: e.target.value })}
                      className="w-full px-4 py-3 bg-dark-bg border border-dark-border rounded-lg focus:border-teamwork-blue focus:outline-none"
                      required
                    >
                      <option value="">Select service</option>
                      <option value="roof-replacement">Roof Replacement</option>
                      <option value="roof-repair">Roof Repair</option>
                      <option value="storm-damage">Storm Damage Assessment</option>
                      <option value="gutters">Gutters</option>
                      <option value="siding">Siding</option>
                      <option value="windows">Windows</option>
                      <option value="full-exterior">Full Exterior</option>
                      <option value="not-sure">Not Sure</option>
                    </select>
                  </div>

                  <div>
                    <label className="block text-sm font-semibold mb-2">
                      Urgency <span className="text-red-500">*</span>
                    </label>
                    <select
                      value={formData.urgency}
                      onChange={(e) => setFormData({ ...formData, urgency: e.target.value })}
                      className="w-full px-4 py-3 bg-dark-bg border border-dark-border rounded-lg focus:border-teamwork-blue focus:outline-none"
                      required
                    >
                      <option value="">Select urgency</option>
                      <option value="active-leak">Active Leak / Emergency</option>
                      <option value="storm-damage">Recent Storm Damage</option>
                      <option value="this-week">This Week</option>
                      <option value="next-week">Next Week</option>
                      <option value="flexible">Flexible / Planning</option>
                    </select>
                  </div>
                </div>

                {/* Preferred Date/Time */}
                <div className="grid md:grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-semibold mb-2">
                      <FiCalendar className="inline w-4 h-4 mr-2" />
                      Preferred Date
                    </label>
                    <input
                      type="date"
                      value={formData.preferredDate}
                      onChange={(e) => setFormData({ ...formData, preferredDate: e.target.value })}
                      className="w-full px-4 py-3 bg-dark-bg border border-dark-border rounded-lg focus:border-teamwork-blue focus:outline-none"
                    />
                  </div>

                  <div>
                    <label className="block text-sm font-semibold mb-2">
                      <FiClock className="inline w-4 h-4 mr-2" />
                      Preferred Time
                    </label>
                    <select
                      value={formData.preferredTime}
                      onChange={(e) => setFormData({ ...formData, preferredTime: e.target.value })}
                      className="w-full px-4 py-3 bg-dark-bg border border-dark-border rounded-lg focus:border-teamwork-blue focus:outline-none"
                    >
                      <option value="">Any time</option>
                      <option value="morning">Morning (8am - 12pm)</option>
                      <option value="afternoon">Afternoon (12pm - 5pm)</option>
                      <option value="evening">Evening (after 5pm)</option>
                    </select>
                  </div>
                </div>

                {/* Notes */}
                <div>
                  <label className="block text-sm font-semibold mb-2">
                    Additional Notes or Questions
                  </label>
                  <textarea
                    value={formData.notes}
                    onChange={(e) => setFormData({ ...formData, notes: e.target.value })}
                    rows={4}
                    placeholder="Tell us more about what you need..."
                    className="w-full px-4 py-3 bg-dark-bg border border-dark-border rounded-lg focus:border-teamwork-blue focus:outline-none"
                  />
                </div>

                {/* Photo Upload Info */}
                <div className="bg-dark-bg border border-dark-border rounded-lg p-4">
                  <h4 className="font-semibold mb-2 flex items-center">
                    <FiCheckCircle className="w-5 h-5 text-teamwork-blue mr-2" />
                    Have photos?
                  </h4>
                  <p className="text-sm text-gray-400">
                    Text photos to <a href="sms:9133963717" className="text-teamwork-blue hover:underline">913-396-3717</a> or email them after booking
                  </p>
                </div>

                <button type="submit" className="btn-primary w-full">
                  Request Same-Week Inspection
                </button>

                <p className="text-xs text-gray-500 text-center">
                  By submitting, you agree to receive calls/texts from Teamwork Roofing Services. We respect your privacy.
                </p>
              </form>
            </div>

            {/* Sidebar */}
            <div className="space-y-6">
              {/* What to Expect */}
              <div className="card">
                <h3 className="heading-4 mb-4">What to Expect</h3>
                <div className="space-y-4">
                  <div className="flex items-start space-x-3">
                    <div className="w-8 h-8 rounded-full bg-teamwork-blue/10 flex items-center justify-center flex-shrink-0">
                      <span className="text-teamwork-blue font-bold">1</span>
                    </div>
                    <div>
                      <h4 className="font-semibold text-sm">Fast Confirmation</h4>
                      <p className="text-xs text-gray-400">We'll call or text within 24 hours</p>
                    </div>
                  </div>

                  <div className="flex items-start space-x-3">
                    <div className="w-8 h-8 rounded-full bg-teamwork-blue/10 flex items-center justify-center flex-shrink-0">
                      <span className="text-teamwork-blue font-bold">2</span>
                    </div>
                    <div>
                      <h4 className="font-semibold text-sm">Same-Week Inspection</h4>
                      <p className="text-xs text-gray-400">Scheduled at your convenience</p>
                    </div>
                  </div>

                  <div className="flex items-start space-x-3">
                    <div className="w-8 h-8 rounded-full bg-teamwork-blue/10 flex items-center justify-center flex-shrink-0">
                      <span className="text-teamwork-blue font-bold">3</span>
                    </div>
                    <div>
                      <h4 className="font-semibold text-sm">Photo Documentation</h4>
                      <p className="text-xs text-gray-400">Complete visual proof included</p>
                    </div>
                  </div>

                  <div className="flex items-start space-x-3">
                    <div className="w-8 h-8 rounded-full bg-teamwork-blue/10 flex items-center justify-center flex-shrink-0">
                      <span className="text-teamwork-blue font-bold">4</span>
                    </div>
                    <div>
                      <h4 className="font-semibold text-sm">Clear Options</h4>
                      <p className="text-xs text-gray-400">Honest pricing and recommendations</p>
                    </div>
                  </div>
                </div>
              </div>

              {/* Contact */}
              <div className="card bg-gradient-to-br from-teamwork-blue to-blue-700">
                <h3 className="heading-4 mb-4">Need Immediate Help?</h3>
                <p className="text-blue-100 text-sm mb-4">
                  Active leak or emergency? Call us now.
                </p>
                <a href="tel:9133963717" className="btn-primary bg-white text-teamwork-blue hover:bg-gray-100 w-full text-center block">
                  Call 913-396-3717
                </a>
              </div>
            </div>
          </div>
        </div>
      </section>

      <PromiseStrip />
    </>
  )
}
