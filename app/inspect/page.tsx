'use client'

import { useEffect, Suspense } from 'react'
import { useSearchParams } from 'next/navigation'
import { FiCalendar, FiPhone } from 'react-icons/fi'

function InspectContent() {
  const searchParams = useSearchParams()
  const source = searchParams.get('src') || 'direct'

  useEffect(() => {
    // Track page view with source parameter
    if (typeof window !== 'undefined' && (window as any)._hsq) {
      ;(window as any)._hsq.push(['setPath', `/inspect?src=${source}`])
      ;(window as any)._hsq.push(['trackPageView'])
    }
  }, [source])

  const handleBookingClick = () => {
    // Track custom event when booking button is clicked
    if (typeof window !== 'undefined' && (window as any)._hsq) {
      ;(window as any)._hsq.push([
        'trackCustomBehavioralEvent',
        {
          name: 'booking_initiated',
          properties: {
            source: source,
            page: '/inspect'
          }
        }
      ])
    }
  }

  return (
    <div className="min-h-screen bg-light-bg">
      {/* Header Section */}
      <section className="section-padding bg-gradient-to-br from-teamwork-green to-green-700">
        <div className="container-custom max-w-2xl text-center">
          <h1 className="heading-1 text-white mb-4">
            Book a Free Roof Inspection
          </h1>
          <p className="text-xl text-green-50 mb-8">
            Free roof inspection with photo documentation for insurance claims. Local Kansas City crew ready to serve.
          </p>

          {/* Primary CTA Buttons */}
          <div className="flex flex-col sm:flex-row gap-4 justify-center mb-6">
            {/* Call Button */}
            <a
              href="tel:+19132779925"
              onClick={handleBookingClick}
              className="btn-primary bg-white text-teamwork-green hover:bg-gray-100 flex items-center justify-center gap-2 text-lg py-4 px-8"
            >
              <FiPhone className="w-6 h-6" />
              Call (913) 277-9925
            </a>

            {/* Schedule Online Button */}
            <a
              href="https://calendar.app.google/ojMPE3CEdiNJXJEk9"
              target="_blank"
              rel="noopener noreferrer"
              onClick={handleBookingClick}
              className="btn-secondary border-white text-white hover:bg-white hover:text-teamwork-green flex items-center justify-center gap-2 text-lg py-4 px-8"
            >
              <FiCalendar className="w-6 h-6" />
              Pick a Time
            </a>
          </div>
        </div>
      </section>

      {/* Calendar Embed Section */}
      <section className="section-padding">
        <div className="container-custom max-w-4xl">
          <div className="card">
            <h2 className="heading-3 text-center mb-6">Choose Your Inspection Time</h2>

            {/* Google Calendar Embed - iframe with fallback */}
            <div className="relative w-full" style={{ paddingBottom: '80%', minHeight: '600px' }}>
              <iframe
                src="https://calendar.app.google/ojMPE3CEdiNJXJEk9"
                className="absolute top-0 left-0 w-full h-full border-0 rounded-lg"
                title="Schedule Free Roof Inspection"
                onError={(e) => {
                  // If iframe fails to load, hide it and show message
                  e.currentTarget.style.display = 'none'
                  const fallback = document.getElementById('calendar-fallback')
                  if (fallback) fallback.style.display = 'block'
                }}
              />

              {/* Fallback message if iframe doesn't work */}
              <div id="calendar-fallback" className="hidden text-center py-12">
                <p className="text-text-secondary mb-6">
                  Click the button below to open the booking calendar in a new window
                </p>
                <a
                  href="https://calendar.app.google/ojMPE3CEdiNJXJEk9"
                  target="_blank"
                  rel="noopener noreferrer"
                  onClick={handleBookingClick}
                  className="btn-primary inline-flex items-center gap-2"
                >
                  <FiCalendar className="w-5 h-5" />
                  Open Calendar
                </a>
              </div>
            </div>

            {/* Additional Info */}
            <div className="mt-8 pt-6 border-t border-light-border">
              <h3 className="font-semibold text-center mb-4">What to Expect</h3>
              <div className="grid sm:grid-cols-3 gap-4 text-sm text-text-secondary">
                <div className="text-center">
                  <div className="w-12 h-12 rounded-full bg-teamwork-green/10 flex items-center justify-center mx-auto mb-2">
                    <span className="text-teamwork-green font-bold text-lg">1</span>
                  </div>
                  <p>Pick your time</p>
                </div>
                <div className="text-center">
                  <div className="w-12 h-12 rounded-full bg-teamwork-green/10 flex items-center justify-center mx-auto mb-2">
                    <span className="text-teamwork-green font-bold text-lg">2</span>
                  </div>
                  <p>Free inspection</p>
                </div>
                <div className="text-center">
                  <div className="w-12 h-12 rounded-full bg-teamwork-green/10 flex items-center justify-center mx-auto mb-2">
                    <span className="text-teamwork-green font-bold text-lg">3</span>
                  </div>
                  <p>Insurance help</p>
                </div>
              </div>
            </div>
          </div>

          {/* Source Tracking Info (hidden, for HubSpot) */}
          <input type="hidden" id="booking-source" value={source} />
        </div>
      </section>
    </div>
  )
}

export default function InspectPage() {
  return (
    <Suspense fallback={
      <div className="min-h-screen bg-light-bg flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-teamwork-green mx-auto mb-4"></div>
          <p className="text-text-secondary">Loading...</p>
        </div>
      </div>
    }>
      <InspectContent />
    </Suspense>
  )
}
