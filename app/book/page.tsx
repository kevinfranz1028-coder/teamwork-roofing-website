'use client'

import { FiClock, FiCheckCircle } from 'react-icons/fi'
import PromiseStrip from '@/components/PromiseStrip'
import BookInspectionForm from '@/components/forms/BookInspectionForm'

export default function BookPage() {
  return (
    <>
      <section className="section-padding bg-light-bg">
        <div className="container-custom max-w-4xl">
          {/* Header */}
          <div className="text-center mb-12">
            <h1 className="heading-1 mb-4">Book Your Same-Week Inspection</h1>
            <p className="text-xl text-text-secondary mb-6">
              Fast, professional, photo-documented — we'll schedule within the same week
            </p>
            <div className="inline-flex items-center space-x-2 bg-teamwork-blue/10 border border-teamwork-blue px-4 py-2 rounded-lg">
              <FiClock className="w-5 h-5 text-teamwork-blue" />
              <span className="text-teamwork-blue font-semibold">Same-Week Promise</span>
            </div>
          </div>

          <div className="grid lg:grid-cols-3 gap-8">
            {/* HubSpot Form */}
            <div className="lg:col-span-2">
              <BookInspectionForm />
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
                      <p className="text-xs text-text-secondary">We'll call or text within 24 hours</p>
                    </div>
                  </div>

                  <div className="flex items-start space-x-3">
                    <div className="w-8 h-8 rounded-full bg-teamwork-blue/10 flex items-center justify-center flex-shrink-0">
                      <span className="text-teamwork-blue font-bold">2</span>
                    </div>
                    <div>
                      <h4 className="font-semibold text-sm">Same-Week Inspection</h4>
                      <p className="text-xs text-text-secondary">Scheduled at your convenience</p>
                    </div>
                  </div>

                  <div className="flex items-start space-x-3">
                    <div className="w-8 h-8 rounded-full bg-teamwork-blue/10 flex items-center justify-center flex-shrink-0">
                      <span className="text-teamwork-blue font-bold">3</span>
                    </div>
                    <div>
                      <h4 className="font-semibold text-sm">Photo Documentation</h4>
                      <p className="text-xs text-text-secondary">Complete visual proof included</p>
                    </div>
                  </div>

                  <div className="flex items-start space-x-3">
                    <div className="w-8 h-8 rounded-full bg-teamwork-blue/10 flex items-center justify-center flex-shrink-0">
                      <span className="text-teamwork-blue font-bold">4</span>
                    </div>
                    <div>
                      <h4 className="font-semibold text-sm">Clear Options</h4>
                      <p className="text-xs text-text-secondary">Honest pricing and recommendations</p>
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

              {/* Photo Upload Info */}
              <div className="card">
                <h4 className="font-semibold mb-2 flex items-center">
                  <FiCheckCircle className="w-5 h-5 text-teamwork-blue mr-2" />
                  Have photos?
                </h4>
                <p className="text-sm text-text-secondary">
                  Text photos to <a href="sms:9133963717" className="text-teamwork-blue hover:underline">913-396-3717</a> or email them after booking
                </p>
              </div>
            </div>
          </div>
        </div>
      </section>

      <PromiseStrip />
    </>
  )
}
