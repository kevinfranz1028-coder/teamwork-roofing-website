import Link from 'next/link'
import Image from 'next/image'
import { FiHome, FiCloudRain, FiDroplet, FiLayers, FiSquare, FiCheckCircle, FiStar, FiPhone, FiAward, FiShield, FiClock, FiCamera, FiArrowRight, FiTool, FiUsers, FiFileText } from 'react-icons/fi'
import PromiseStrip from '@/components/PromiseStrip'
import CTABand from '@/components/CTABand'
import BrandsWeInstall from '@/components/BrandsWeInstall'

export default function Home() {
  const services = [
    {
      icon: FiHome,
      title: 'Roof Replacement',
      shortDesc: 'Complete systems',
      frontDesc: 'Premium roof systems with expert installation',
      backDesc: 'Full tear-off and replacement with manufacturer-grade materials. GAF, CertainTeed, Owens Corning, and more. Lifetime warranties available.',
      href: '/services/roof-replacement/'
    },
    {
      icon: FiTool,
      title: 'Roof Repair',
      shortDesc: 'Fast repairs',
      frontDesc: 'Reliable repairs that extend your roof\'s life',
      backDesc: 'Storm damage, leaks, missing shingles, and aging roofs. Same-week service with photo documentation of all repairs.',
      href: '/services/roof-repair/'
    },
    {
      icon: FiCloudRain,
      title: 'Storm Damage',
      shortDesc: 'Full inspection',
      frontDesc: 'Thorough inspection and insurance assistance',
      backDesc: 'Complete storm damage assessment with detailed photo reports. We handle insurance claims and work directly with adjusters.',
      href: '/storm/'
    },
    {
      icon: FiDroplet,
      title: 'Gutters',
      shortDesc: 'Seamless systems',
      frontDesc: 'Seamless gutters, guards, and repair',
      backDesc: 'Custom-fitted seamless gutters, leaf guards, and downspout systems. Protect your foundation and landscaping.',
      href: '/services/gutters/'
    },
    {
      icon: FiLayers,
      title: 'Siding',
      shortDesc: 'Beautiful protection',
      frontDesc: 'Durable siding that beautifies your home',
      backDesc: 'Vinyl, fiber cement, and composite siding. Energy-efficient options with superior weather protection.',
      href: '/services/siding/'
    },
    {
      icon: FiSquare,
      title: 'Windows',
      shortDesc: 'Energy efficient',
      frontDesc: 'Energy-efficient window replacements',
      backDesc: 'Double and triple-pane windows that reduce energy bills. Professional installation with weatherproof sealing.',
      href: '/services/windows/'
    }
  ]

  const processSteps = [
    {
      number: '01',
      icon: FiPhone,
      title: 'Contact Us',
      shortDesc: 'Same-day response',
      frontDesc: 'Call, text, or book online',
      backDesc: 'Reach us by phone, text, or our online booking form. We respond the same day and schedule your inspection within the week.'
    },
    {
      number: '02',
      icon: FiClock,
      title: 'Same-Week Inspection',
      shortDesc: 'We arrive fast',
      frontDesc: 'Professional assessment',
      backDesc: 'Our certified team arrives within the week with all necessary equipment. We conduct a thorough inspection of your roof and exterior.'
    },
    {
      number: '03',
      icon: FiCamera,
      title: 'Photo Documentation',
      shortDesc: 'See what we see',
      frontDesc: 'Complete transparency',
      backDesc: 'Every inspection includes detailed photos and measurements. You receive a full report showing exactly what we found.'
    },
    {
      number: '04',
      icon: FiFileText,
      title: 'Clear Options',
      shortDesc: 'Honest pricing',
      frontDesc: 'No pressure guidance',
      backDesc: 'We present multiple options with transparent pricing. No hidden fees, no pressure tactics—just honest advice.'
    },
    {
      number: '05',
      icon: FiShield,
      title: 'Expert Installation',
      shortDesc: 'Warranty backed',
      frontDesc: 'Professional execution',
      backDesc: 'Skilled installation with daily cleanup and magnetic sweeps. Site left spotless with full warranty protection.'
    }
  ]

  const reviews = [
    {
      name: 'Sarah M.',
      city: 'Overland Park',
      rating: 5,
      text: 'True to their name — real teamwork. They kept us informed every step, left the property spotless, and the roof looks incredible.'
    },
    {
      name: 'Mike T.',
      city: 'Lenexa',
      rating: 5,
      text: 'After storm damage, they helped with documentation and made the insurance process so much easier. Highly recommend.'
    },
    {
      name: 'Jennifer K.',
      city: 'Olathe',
      rating: 5,
      text: 'Same-week inspection promise delivered! Professional crew, clear communication, and beautiful results.'
    }
  ]

  return (
    <>
      {/* Hero Section - Clean Modern Design */}
      <section className="relative bg-gradient-to-br from-gray-900 via-gray-800 to-gray-900 text-white overflow-hidden">
        {/* Background Pattern */}
        <div className="absolute inset-0 opacity-10">
          <div className="absolute inset-0" style={{
            backgroundImage: `url("data:image/svg+xml,%3Csvg width='60' height='60' viewBox='0 0 60 60' xmlns='http://www.w3.org/2000/svg'%3E%3Cg fill='none' fill-rule='evenodd'%3E%3Cg fill='%23ffffff' fill-opacity='0.4'%3E%3Cpath d='M36 34v-4h-2v4h-4v2h4v4h2v-4h4v-2h-4zm0-30V0h-2v4h-4v2h4v4h2V6h4V4h-4zM6 34v-4H4v4H0v2h4v4h2v-4h4v-2H6zM6 4V0H4v4H0v2h4v4h2V6h4V4H6z'/%3E%3C/g%3E%3C/g%3E%3C/svg%3E")`
          }}></div>
        </div>

        <div className="container-custom relative">
          <div className="py-20 md:py-28 lg:py-32">
            <div className="max-w-4xl">
              {/* Trust Badge */}
              <div className="inline-flex items-center gap-2 bg-white/10 backdrop-blur-md px-4 py-2 rounded-full mb-6 border border-white/20">
                <FiShield className="w-4 h-4 text-teamwork-blue" />
                <span className="text-sm font-semibold">Kansas City's Trusted Roofing Partner Since 2009</span>
              </div>

              {/* Main Headline */}
              <h1 className="text-4xl md:text-5xl lg:text-6xl font-bold mb-6 leading-tight">
                Roofing & Exteriors —<br />
                <span className="text-teamwork-blue">The Teamwork Way</span>
              </h1>

              <p className="text-lg md:text-xl text-gray-300 mb-8 max-w-2xl leading-relaxed">
                Premium roofing, gutters, siding, and windows for Kansas City Metro. Same-week inspections, photo documentation, and a clean site guarantee.
              </p>

              {/* CTA Buttons */}
              <div className="flex flex-col sm:flex-row gap-4 mb-12">
                <Link
                  href="/book/"
                  className="inline-flex items-center justify-center px-8 py-4 bg-teamwork-blue text-white font-semibold rounded-lg hover:bg-[#0094CC] transition-all shadow-lg hover:shadow-xl transform hover:scale-[1.02]"
                >
                  Schedule Free Inspection
                  <FiArrowRight className="ml-2 w-5 h-5" />
                </Link>
                <a
                  href="tel:9133963717"
                  className="inline-flex items-center justify-center px-8 py-4 bg-white text-gray-900 font-semibold rounded-lg hover:bg-gray-100 transition-all shadow-lg"
                >
                  <FiPhone className="mr-2 w-5 h-5 text-teamwork-blue" />
                  (913) 396-3717
                </a>
              </div>

              {/* Trust Icons */}
              <div className="flex flex-wrap gap-6 pt-8 border-t border-white/20">
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 rounded-lg bg-teamwork-blue/20 flex items-center justify-center">
                    <FiCheckCircle className="w-5 h-5 text-teamwork-blue" />
                  </div>
                  <span className="text-sm font-medium">Licensed & Insured</span>
                </div>
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 rounded-lg bg-teamwork-blue/20 flex items-center justify-center">
                    <FiClock className="w-5 h-5 text-teamwork-blue" />
                  </div>
                  <span className="text-sm font-medium">Same-Week Service</span>
                </div>
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 rounded-lg bg-teamwork-blue/20 flex items-center justify-center">
                    <FiCamera className="w-5 h-5 text-teamwork-blue" />
                  </div>
                  <span className="text-sm font-medium">Photo Documented</span>
                </div>
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 rounded-lg bg-teamwork-blue/20 flex items-center justify-center">
                    <FiShield className="w-5 h-5 text-teamwork-blue" />
                  </div>
                  <span className="text-sm font-medium">Warranty Backed</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Services Grid with Flip Cards */}
      <section className="section-padding bg-white">
        <div className="container-custom">
          <div className="max-w-3xl mx-auto text-center mb-16">
            <h2 className="heading-2 mb-4">Complete Roofing & Exterior Services</h2>
            <p className="text-lg text-text-secondary">
              From emergency repairs to full replacements, we protect Kansas City homes with quality workmanship and honest pricing.
            </p>
          </div>

          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6 max-w-6xl mx-auto">
            {services.map((service, index) => {
              const Icon = service.icon
              return (
                <div key={index} className="group [perspective:1000px] h-[280px]">
                  <div className="relative w-full h-full transition-transform duration-700 [transform-style:preserve-3d] group-hover:[transform:rotateY(180deg)]">
                    {/* Front of Card */}
                    <div className="absolute inset-0 [backface-visibility:hidden]">
                      <div className="h-full bg-white border border-gray-200 rounded-xl p-6 flex flex-col justify-between shadow-md hover:shadow-xl transition-shadow">
                        <div>
                          <div className="w-14 h-14 rounded-xl bg-teamwork-blue/10 flex items-center justify-center mb-4">
                            <Icon className="w-7 h-7 text-teamwork-blue" />
                          </div>
                          <h3 className="text-xl font-semibold mb-2">{service.title}</h3>
                          <p className="text-text-secondary leading-relaxed">{service.frontDesc}</p>
                        </div>
                        <div className="text-teamwork-blue text-sm font-medium flex items-center mt-4">
                          <span>Hover to learn more</span>
                          <FiArrowRight className="ml-2 w-4 h-4" />
                        </div>
                      </div>
                    </div>

                    {/* Back of Card */}
                    <div className="absolute inset-0 [backface-visibility:hidden] [transform:rotateY(180deg)]">
                      <div className="h-full bg-teamwork-blue text-white rounded-xl p-6 flex flex-col justify-between shadow-xl">
                        <div>
                          <div className="w-14 h-14 rounded-xl bg-white/20 flex items-center justify-center mb-4">
                            <Icon className="w-7 h-7 text-white" />
                          </div>
                          <h3 className="text-xl font-bold mb-3">{service.title}</h3>
                          <p className="text-white/90 text-sm leading-relaxed">{service.backDesc}</p>
                        </div>
                        <Link
                          href={service.href}
                          className="inline-flex items-center justify-center px-6 py-3 bg-white text-teamwork-blue font-semibold rounded-lg hover:bg-gray-100 transition-colors mt-4"
                        >
                          Learn More
                          <FiArrowRight className="ml-2 w-4 h-4" />
                        </Link>
                      </div>
                    </div>
                  </div>
                </div>
              )
            })}
          </div>

          <div className="text-center mt-12">
            <Link href="/service-areas/" className="inline-flex items-center text-teamwork-blue hover:text-[#0094CC] font-medium">
              View All Service Areas <FiArrowRight className="ml-2 w-5 h-5" />
            </Link>
          </div>
        </div>
      </section>

      {/* Process Timeline with Flip Cards */}
      <section className="py-16 bg-gray-50">
        <div className="container-custom">
          <div className="max-w-3xl mx-auto text-center mb-10">
            <h2 className="heading-2 mb-3">How It Works</h2>
            <p className="text-text-secondary">
              Five simple steps from first contact to warranty activation. Hover over each step to see details.
            </p>
          </div>

          <div className="max-w-4xl mx-auto relative">
            {/* Timeline Line */}
            <div className="hidden lg:block absolute left-1/2 top-0 transform -translate-x-1/2 h-full w-0.5 bg-gradient-to-b from-teamwork-blue via-teamwork-blue to-transparent"></div>

            <div className="space-y-4">
              {processSteps.map((step, index) => {
                const Icon = step.icon
                const isEven = index % 2 === 0

                return (
                  <div key={index} className={`flex items-center ${isEven ? 'lg:flex-row' : 'lg:flex-row-reverse'} gap-4`}>
                    {/* Content - Flip Card */}
                    <div className="flex-1 group [perspective:1000px]">
                      <div className="relative w-full h-[160px] transition-transform duration-700 [transform-style:preserve-3d] group-hover:[transform:rotateY(180deg)]">
                        {/* Front */}
                        <div className="absolute inset-0 [backface-visibility:hidden]">
                          <div className="h-full bg-white rounded-lg p-4 shadow-md border border-gray-200 hover:border-teamwork-blue transition-colors">
                            <div className="flex items-start gap-3 h-full">
                              <div className="w-10 h-10 rounded-lg bg-teamwork-blue flex items-center justify-center flex-shrink-0">
                                <Icon className="w-5 h-5 text-white" />
                              </div>
                              <div className="flex-1">
                                <div className="flex items-baseline gap-2 mb-1">
                                  <span className="text-xs font-bold text-teamwork-blue tracking-wider">{step.number}</span>
                                  <h3 className="text-lg font-bold">{step.title}</h3>
                                </div>
                                <p className="text-text-secondary text-sm mb-2">{step.frontDesc}</p>
                                <p className="text-xs text-teamwork-blue font-medium">Hover for details →</p>
                              </div>
                            </div>
                          </div>
                        </div>

                        {/* Back */}
                        <div className="absolute inset-0 [backface-visibility:hidden] [transform:rotateY(180deg)]">
                          <div className="h-full bg-gradient-to-br from-teamwork-blue to-[#0094CC] text-white rounded-lg p-4 shadow-xl flex flex-col justify-between">
                            <div>
                              <div className="flex items-center gap-2 mb-2">
                                <div className="w-8 h-8 rounded-lg bg-white/20 flex items-center justify-center">
                                  <Icon className="w-4 h-4 text-white" />
                                </div>
                                <span className="text-xs font-bold tracking-wider opacity-80">{step.number}</span>
                              </div>
                              <h3 className="text-lg font-bold mb-2">{step.title}</h3>
                              <p className="text-white/95 text-sm leading-relaxed">{step.backDesc}</p>
                            </div>
                            <div className="mt-2 pt-2 border-t border-white/20">
                              <p className="text-xs text-white/70">{step.shortDesc}</p>
                            </div>
                          </div>
                        </div>
                      </div>
                    </div>

                    {/* Center Number Badge */}
                    <div className="hidden lg:flex flex-shrink-0 w-12 h-12 rounded-full bg-teamwork-blue text-white items-center justify-center font-bold text-lg shadow-lg border-4 border-gray-50 z-10">
                      {index + 1}
                    </div>

                    {/* Spacer for alternating layout */}
                    <div className="hidden lg:block flex-1"></div>
                  </div>
                )
              })}
            </div>
          </div>
        </div>
      </section>

      {/* Reviews */}
      <section className="section-padding bg-white">
        <div className="container-custom">
          <div className="max-w-3xl mx-auto text-center mb-16">
            <h2 className="heading-2 mb-4">What Kansas City Homeowners Say</h2>
            <p className="text-lg text-text-secondary">Real partnerships, real results</p>
          </div>

          <div className="grid md:grid-cols-3 gap-8 max-w-6xl mx-auto">
            {reviews.map((review, index) => (
              <div key={index} className="bg-white rounded-xl p-6 shadow-lg border border-gray-100 hover:shadow-xl hover:border-teamwork-blue transition-all">
                <div className="flex gap-1 mb-4">
                  {[...Array(review.rating)].map((_, i) => (
                    <FiStar key={i} className="w-5 h-5 text-yellow-400 fill-current" />
                  ))}
                </div>
                <p className="text-text-secondary mb-6 leading-relaxed italic">"{review.text}"</p>
                <div className="flex items-center gap-3 pt-4 border-t border-gray-200">
                  <div className="w-12 h-12 rounded-full bg-teamwork-blue/10 flex items-center justify-center font-bold text-teamwork-blue">
                    {review.name.charAt(0)}
                  </div>
                  <div>
                    <div className="font-semibold">{review.name}</div>
                    <div className="text-sm text-text-secondary">{review.city}, KS</div>
                  </div>
                </div>
              </div>
            ))}
          </div>

          <div className="text-center mt-12">
            <Link href="/reviews/" className="inline-flex items-center btn-secondary">
              Read All Reviews <FiArrowRight className="ml-2 w-5 h-5" />
            </Link>
          </div>
        </div>
      </section>

      <BrandsWeInstall variant="full" />

      <CTABand title="Ready to Protect Your Home?" subtitle="Same-week inspections available. Book online or call now." />
    </>
  )
}
