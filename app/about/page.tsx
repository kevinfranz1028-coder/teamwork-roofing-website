import { FiShield, FiClock, FiCheckCircle, FiCamera, FiDollarSign } from 'react-icons/fi'
import CTABand from '@/components/CTABand'

export const metadata = {
  title: 'About Us | Teamwork Roofing Services Kansas City',
  description: 'Learn about Teamwork Roofing Services and our commitment to partnership, quality, and transparency in Kansas City Metro.',
}

export default function AboutPage() {
  return (
    <>
      <section className="section-padding bg-dark-bg">
        <div className="container-custom">
          <div className="max-w-3xl mx-auto text-center mb-16">
            <h1 className="heading-1 mb-6">
              Built on <span className="text-teamwork-blue">Teamwork</span>
            </h1>
            <p className="text-xl text-gray-400">
              More than a name — it's our commitment. From day one, you're a partner, not a transaction.
            </p>
          </div>

          <div className="max-w-4xl mx-auto space-y-12">
            {/* What Teamwork Means */}
            <div className="card">
              <h2 className="heading-3 mb-6">What "Teamwork" Means to Us</h2>
              <div className="space-y-4 text-gray-400">
                <p>
                  Every roofing company talks about quality. We do quality differently — with you as part of the team.
                </p>
                <p>
                  That means showing you the photos, explaining your options, respecting your property, and delivering on our promises. No pressure, no surprises, no cutting corners.
                </p>
                <p>
                  It means if repair makes sense, we'll repair it honestly. If replacement is smarter, we'll explain why with evidence you can see.
                </p>
                <p>
                  Teamwork means you can trust us to treat your home like our own — because in a partnership, your success is our success.
                </p>
              </div>
            </div>

            {/* The 5 Promises */}
            <div>
              <h2 className="heading-3 mb-8 text-center">The 5 Promises That Define Us</h2>
              <div className="grid md:grid-cols-2 lg:grid-cols-5 gap-6">
                <div className="card text-center">
                  <FiShield className="w-12 h-12 text-teamwork-blue mx-auto mb-4" />
                  <h4 className="font-semibold mb-2">Teamwork Warranty</h4>
                  <p className="text-sm text-gray-400">Backed by our partnership commitment</p>
                </div>

                <div className="card text-center">
                  <FiClock className="w-12 h-12 text-teamwork-blue mx-auto mb-4" />
                  <h4 className="font-semibold mb-2">Same-Week Inspection</h4>
                  <p className="text-sm text-gray-400">Fast response guaranteed</p>
                </div>

                <div className="card text-center">
                  <FiCheckCircle className="w-12 h-12 text-teamwork-blue mx-auto mb-4" />
                  <h4 className="font-semibold mb-2">Clean Site Guarantee</h4>
                  <p className="text-sm text-gray-400">Your property protected</p>
                </div>

                <div className="card text-center">
                  <FiCamera className="w-12 h-12 text-teamwork-blue mx-auto mb-4" />
                  <h4 className="font-semibold mb-2">Photo-Proof Inspection</h4>
                  <p className="text-sm text-gray-400">Complete documentation</p>
                </div>

                <div className="card text-center">
                  <FiDollarSign className="w-12 h-12 text-teamwork-blue mx-auto mb-4" />
                  <h4 className="font-semibold mb-2">Teamwork Financing</h4>
                  <p className="text-sm text-gray-400">Flexible payment options</p>
                </div>
              </div>
            </div>

            {/* Service Area */}
            <div className="card bg-dark-surface">
              <h2 className="heading-3 mb-4">Serving Kansas City Metro</h2>
              <p className="text-gray-400 mb-4">
                We proudly serve homeowners across the Kansas City Metro area with the same commitment to partnership and quality.
              </p>
              <div className="grid md:grid-cols-2 gap-4 text-gray-500">
                <div>
                  <h4 className="font-semibold text-white mb-2">Kansas</h4>
                  <ul className="space-y-1 text-sm">
                    <li>Overland Park</li>
                    <li>Olathe</li>
                    <li>Lenexa</li>
                    <li>Shawnee</li>
                    <li>Leawood</li>
                    <li>Prairie Village</li>
                    <li>Mission</li>
                    <li>Merriam</li>
                    <li>Gardner</li>
                    <li>Spring Hill</li>
                    <li>De Soto</li>
                    <li>And nearby areas</li>
                  </ul>
                </div>
                <div>
                  <h4 className="font-semibold text-white mb-2">Missouri</h4>
                  <ul className="space-y-1 text-sm">
                    <li>Kansas City</li>
                    <li>Lee's Summit</li>
                    <li>Independence</li>
                    <li>Blue Springs</li>
                    <li>Raytown</li>
                    <li>Grandview</li>
                    <li>Belton</li>
                    <li>Liberty</li>
                    <li>Gladstone</li>
                    <li>North Kansas City</li>
                    <li>And nearby areas</li>
                  </ul>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      <CTABand title="Experience the Teamwork Difference" subtitle="Book your same-week inspection and see what partnership feels like" />
    </>
  )
}
