import { FiShield, FiClock, FiCheckCircle, FiCamera, FiDollarSign } from 'react-icons/fi'
import CTABand from '@/components/CTABand'

export const metadata = {
  title: 'About Us | Teamwork Roofing Services Kansas City',
  description: 'Learn about Teamwork Roofing Services and our commitment to partnership, quality, and transparency in Kansas City Metro.',
}

export default function AboutPage() {
  return (
    <>
      <section className="section-padding bg-light-bg">
        <div className="container-custom">
          <div className="max-w-3xl mx-auto text-center mb-16">
            <h1 className="heading-1 mb-6">
              Built on <span className="text-teamwork-green">Teamwork</span>
            </h1>
            <p className="text-xl text-text-secondary">
              More than a name — it's our commitment. From day one, you're a partner, not a transaction.
            </p>
          </div>

          <div className="max-w-4xl mx-auto space-y-12">
            {/* What Teamwork Means */}
            <div className="card">
              <h2 className="heading-3 mb-6">What "Teamwork" Means to Us</h2>
              <div className="space-y-4 text-text-secondary">
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
                <div className="group [perspective:1000px]">
                  <div className="relative w-full h-[200px] transition-transform duration-700 [transform-style:preserve-3d] group-hover:[transform:rotateY(180deg)]">
                    <div className="absolute inset-0 [backface-visibility:hidden]">
                      <div className="h-full card text-center flex flex-col items-center justify-center hover:border-teamwork-green transition-colors">
                        <FiShield className="w-12 h-12 text-teamwork-green mb-4" />
                        <h4 className="font-semibold mb-2">Teamwork Warranty</h4>
                        <p className="text-xs text-teamwork-green font-medium">Hover for details →</p>
                      </div>
                    </div>
                    <div className="absolute inset-0 [backface-visibility:hidden] [transform:rotateY(180deg)]">
                      <div className="h-full bg-gradient-to-br from-teamwork-green to-[#0094CC] text-white rounded-lg p-4 flex flex-col items-center justify-center text-center">
                        <FiShield className="w-10 h-10 mb-3 opacity-90" />
                        <h4 className="font-bold mb-2 text-sm">Teamwork Warranty</h4>
                        <p className="text-xs text-white/90">Backed by our partnership commitment and workmanship guarantee</p>
                      </div>
                    </div>
                  </div>
                </div>

                <div className="group [perspective:1000px]">
                  <div className="relative w-full h-[200px] transition-transform duration-700 [transform-style:preserve-3d] group-hover:[transform:rotateY(180deg)]">
                    <div className="absolute inset-0 [backface-visibility:hidden]">
                      <div className="h-full card text-center flex flex-col items-center justify-center hover:border-teamwork-green transition-colors">
                        <FiClock className="w-12 h-12 text-teamwork-green mb-4" />
                        <h4 className="font-semibold mb-2">Same-Week Inspection</h4>
                        <p className="text-xs text-teamwork-green font-medium">Hover for details →</p>
                      </div>
                    </div>
                    <div className="absolute inset-0 [backface-visibility:hidden] [transform:rotateY(180deg)]">
                      <div className="h-full bg-gradient-to-br from-teamwork-green to-[#0094CC] text-white rounded-lg p-4 flex flex-col items-center justify-center text-center">
                        <FiClock className="w-10 h-10 mb-3 opacity-90" />
                        <h4 className="font-bold mb-2 text-sm">Same-Week Inspection</h4>
                        <p className="text-xs text-white/90">Fast response guaranteed — inspections scheduled within the same week</p>
                      </div>
                    </div>
                  </div>
                </div>

                <div className="group [perspective:1000px]">
                  <div className="relative w-full h-[200px] transition-transform duration-700 [transform-style:preserve-3d] group-hover:[transform:rotateY(180deg)]">
                    <div className="absolute inset-0 [backface-visibility:hidden]">
                      <div className="h-full card text-center flex flex-col items-center justify-center hover:border-teamwork-green transition-colors">
                        <FiCheckCircle className="w-12 h-12 text-teamwork-green mb-4" />
                        <h4 className="font-semibold mb-2">Clean Site Guarantee</h4>
                        <p className="text-xs text-teamwork-green font-medium">Hover for details →</p>
                      </div>
                    </div>
                    <div className="absolute inset-0 [backface-visibility:hidden] [transform:rotateY(180deg)]">
                      <div className="h-full bg-gradient-to-br from-teamwork-green to-[#0094CC] text-white rounded-lg p-4 flex flex-col items-center justify-center text-center">
                        <FiCheckCircle className="w-10 h-10 mb-3 opacity-90" />
                        <h4 className="font-bold mb-2 text-sm">Clean Site Guarantee</h4>
                        <p className="text-xs text-white/90">Your property protected with tarps, careful handling, and thorough cleanup</p>
                      </div>
                    </div>
                  </div>
                </div>

                <div className="group [perspective:1000px]">
                  <div className="relative w-full h-[200px] transition-transform duration-700 [transform-style:preserve-3d] group-hover:[transform:rotateY(180deg)]">
                    <div className="absolute inset-0 [backface-visibility:hidden]">
                      <div className="h-full card text-center flex flex-col items-center justify-center hover:border-teamwork-green transition-colors">
                        <FiCamera className="w-12 h-12 text-teamwork-green mb-4" />
                        <h4 className="font-semibold mb-2">Photo-Proof Inspection</h4>
                        <p className="text-xs text-teamwork-green font-medium">Hover for details →</p>
                      </div>
                    </div>
                    <div className="absolute inset-0 [backface-visibility:hidden] [transform:rotateY(180deg)]">
                      <div className="h-full bg-gradient-to-br from-teamwork-green to-[#0094CC] text-white rounded-lg p-4 flex flex-col items-center justify-center text-center">
                        <FiCamera className="w-10 h-10 mb-3 opacity-90" />
                        <h4 className="font-bold mb-2 text-sm">Photo-Proof Inspection</h4>
                        <p className="text-xs text-white/90">Complete documentation so you can see exactly what we see</p>
                      </div>
                    </div>
                  </div>
                </div>

                <div className="group [perspective:1000px]">
                  <div className="relative w-full h-[200px] transition-transform duration-700 [transform-style:preserve-3d] group-hover:[transform:rotateY(180deg)]">
                    <div className="absolute inset-0 [backface-visibility:hidden]">
                      <div className="h-full card text-center flex flex-col items-center justify-center hover:border-teamwork-green transition-colors">
                        <FiDollarSign className="w-12 h-12 text-teamwork-green mb-4" />
                        <h4 className="font-semibold mb-2">Teamwork Financing</h4>
                        <p className="text-xs text-teamwork-green font-medium">Hover for details →</p>
                      </div>
                    </div>
                    <div className="absolute inset-0 [backface-visibility:hidden] [transform:rotateY(180deg)]">
                      <div className="h-full bg-gradient-to-br from-teamwork-green to-[#0094CC] text-white rounded-lg p-4 flex flex-col items-center justify-center text-center">
                        <FiDollarSign className="w-10 h-10 mb-3 opacity-90" />
                        <h4 className="font-bold mb-2 text-sm">Teamwork Financing</h4>
                        <p className="text-xs text-white/90">Flexible payment options to make quality work affordable</p>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>

            {/* Service Area */}
            <div className="card bg-white">
              <h2 className="heading-3 mb-4">Serving Kansas City Metro</h2>
              <p className="text-text-secondary mb-4">
                We proudly serve homeowners across the Kansas City Metro area with the same commitment to partnership and quality.
              </p>
              <div className="grid md:grid-cols-2 gap-4 text-text-muted">
                <div>
                  <h4 className="font-semibold text-text-primary mb-2">Kansas</h4>
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
                  <h4 className="font-semibold text-text-primary mb-2">Missouri</h4>
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
