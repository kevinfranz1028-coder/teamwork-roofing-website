import Link from 'next/link'
import Image from 'next/image'
import { FiHome, FiCloudRain, FiDroplet, FiLayers, FiSquare, FiCheckCircle, FiStar, FiPhone, FiAward, FiShield, FiClock, FiCamera } from 'react-icons/fi'
import PromiseStrip from '@/components/PromiseStrip'
import CTABand from '@/components/CTABand'
import BrandsWeInstall from '@/components/BrandsWeInstall'

export default function Home() {
  const services = [
    {
      icon: FiHome,
      title: 'Roof Replacement',
      description: 'Premium systems installed right',
      href: '/services/roof-replacement/'
    },
    {
      icon: FiHome,
      title: 'Roof Repair',
      description: 'Fast, honest repair solutions',
      href: '/services/roof-repair/'
    },
    {
      icon: FiCloudRain,
      title: 'Storm Damage',
      description: 'Full inspection & documentation',
      href: '/storm/'
    },
    {
      icon: FiDroplet,
      title: 'Gutters',
      description: 'Seamless, guards, and repair',
      href: '/services/gutters/'
    },
    {
      icon: FiLayers,
      title: 'Siding',
      description: 'Protect and beautify your home',
      href: '/services/siding/'
    },
    {
      icon: FiSquare,
      title: 'Windows',
      description: 'Energy-efficient replacements',
      href: '/services/windows/'
    }
  ]

  const processSteps = [
    {
      icon: FiPhone,
      title: 'Call or Book Online',
      description: 'Same-day response guaranteed'
    },
    {
      icon: FiClock,
      title: 'Same-Week Inspection',
      description: 'We arrive fast—your time matters'
    },
    {
      icon: FiCamera,
      title: 'Photo Documentation',
      description: 'See exactly what we see'
    },
    {
      icon: FiCheckCircle,
      title: 'Clear Options & Pricing',
      description: 'Honest guidance, no pressure'
    },
    {
      icon: FiShield,
      title: 'Expert Installation',
      description: 'Clean site, Teamwork Warranty'
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
      {/* Hero Section - Full Screen with Strong Visual Impact */}
      <section className="relative min-h-[85vh] flex items-center overflow-hidden">
        {/* Background with Gradient Overlay - Ready for real image */}
        <div className="absolute inset-0 z-0">
          <div className="absolute inset-0 bg-gradient-to-br from-gray-900/90 via-gray-800/85 to-teamwork-blue/80 z-10"></div>
          {/* Placeholder for background image - will show through gradient */}
          <div className="absolute inset-0 bg-gray-800">
            {/* Subtle pattern for texture */}
            <div className="absolute inset-0 opacity-5" style={{
              backgroundImage: `url("data:image/svg+xml,%3Csvg width='80' height='80' viewBox='0 0 80 80' xmlns='http://www.w3.org/2000/svg'%3E%3Cg fill='none' fill-rule='evenodd'%3E%3Cg fill='%23ffffff' fill-opacity='1'%3E%3Cpath d='M50 50c0-5.523 4.477-10 10-10s10 4.477 10 10-4.477 10-10 10c0 5.523-4.477 10-10 10s-10-4.477-10-10 4.477-10 10-10zM10 10c0-5.523 4.477-10 10-10s10 4.477 10 10-4.477 10-10 10c0 5.523-4.477 10-10 10S0 25.523 0 20s4.477-10 10-10zm10 8c4.418 0 8-3.582 8-8s-3.582-8-8-8-8 3.582-8 8 3.582 8 8 8zm40 40c4.418 0 8-3.582 8-8s-3.582-8-8-8-8 3.582-8 8 3.582 8 8 8z' /%3E%3C/g%3E%3C/g%3E%3C/svg%3E")`
            }}></div>
          </div>
        </div>

        {/* Hero Content */}
        <div className="container-custom relative z-20 py-24">
          <div className="max-w-4xl">
            {/* Small tag above headline */}
            <div className="inline-flex items-center space-x-2 bg-teamwork-blue/20 backdrop-blur-sm px-4 py-2 rounded-full mb-6">
              <FiShield className="w-4 h-4 text-teamwork-blue" />
              <span className="text-sm font-semibold text-white">Kansas City Metro's Trusted Roofing Partner</span>
            </div>

            {/* Main Headline - Larger, More Impactful */}
            <h1 className="text-5xl md:text-6xl lg:text-7xl font-black text-white mb-6 leading-[1.1]">
              Roofing & Exteriors<br />
              <span className="text-teamwork-blue">The Teamwork Way</span>
            </h1>

            {/* Subheadline */}
            <p className="text-xl md:text-2xl text-gray-100 mb-10 max-w-3xl font-medium">
              Same-week inspections. Photo-proof documentation. Clean site guarantee. Your Kansas City home deserves a roofing partner you can trust.
            </p>

            {/* Primary CTAs */}
            <div className="flex flex-col sm:flex-row gap-4 mb-12">
              <Link
                href="/book/"
                className="group inline-flex items-center justify-center px-10 py-5 bg-teamwork-blue text-white font-bold text-lg rounded-lg hover:bg-[#0094CC] transition-all shadow-2xl hover:shadow-teamwork-blue/50 transform hover:scale-105"
              >
                <span>Get Free Inspection</span>
                <svg className="w-5 h-5 ml-2 group-hover:translate-x-1 transition-transform" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                </svg>
              </Link>
              <a
                href="tel:9133963717"
                className="inline-flex items-center justify-center px-10 py-5 bg-white text-gray-900 font-bold text-lg rounded-lg hover:bg-gray-50 transition-all shadow-2xl"
              >
                <FiPhone className="mr-3 text-teamwork-blue" />
                <span className="text-teamwork-blue">(913)</span> 396-3717
              </a>
            </div>

            {/* Trust Bar */}
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4 pt-8 border-t border-white/20">
              <div className="flex items-center space-x-3">
                <div className="w-10 h-10 rounded-full bg-teamwork-blue/20 flex items-center justify-center flex-shrink-0">
                  <FiCheckCircle className="w-5 h-5 text-teamwork-blue" />
                </div>
                <span className="text-white font-medium text-sm">Licensed & Insured</span>
              </div>
              <div className="flex items-center space-x-3">
                <div className="w-10 h-10 rounded-full bg-teamwork-blue/20 flex items-center justify-center flex-shrink-0">
                  <FiClock className="w-5 h-5 text-teamwork-blue" />
                </div>
                <span className="text-white font-medium text-sm">Same-Week Service</span>
              </div>
              <div className="flex items-center space-x-3">
                <div className="w-10 h-10 rounded-full bg-teamwork-blue/20 flex items-center justify-center flex-shrink-0">
                  <FiCamera className="w-5 h-5 text-teamwork-blue" />
                </div>
                <span className="text-white font-medium text-sm">Photo Documented</span>
              </div>
              <div className="flex items-center space-x-3">
                <div className="w-10 h-10 rounded-full bg-teamwork-blue/20 flex items-center justify-center flex-shrink-0">
                  <FiShield className="w-5 h-5 text-teamwork-blue" />
                </div>
                <span className="text-white font-medium text-sm">Warranty Backed</span>
              </div>
            </div>
          </div>
        </div>

        {/* Scroll indicator */}
        <div className="absolute bottom-8 left-1/2 -translate-x-1/2 z-20 animate-bounce">
          <svg className="w-6 h-6 text-white/50" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 14l-7 7m0 0l-7-7m7 7V3" />
          </svg>
        </div>
      </section>

      {/* Services Section - Clean Grid */}
      <section className="section-padding bg-white">
        <div className="container-custom">
          <div className="text-center mb-16">
            <span className="text-teamwork-blue font-bold text-sm uppercase tracking-wider">Complete Solutions</span>
            <h2 className="heading-2 mt-3 mb-4">Our Roofing & Exterior Services</h2>
            <p className="text-xl text-text-secondary max-w-2xl mx-auto">
              From roof replacement to storm repairs, we protect Kansas City homes with quality workmanship
            </p>
          </div>

          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6 max-w-6xl mx-auto">
            {services.map((service, index) => {
              const Icon = service.icon
              return (
                <Link
                  key={index}
                  href={service.href}
                  className="group relative bg-white border-2 border-light-border hover:border-teamwork-blue rounded-xl p-8 transition-all duration-300 hover:shadow-xl"
                >
                  <div className="w-16 h-16 rounded-lg bg-teamwork-blue/10 group-hover:bg-teamwork-blue flex items-center justify-center mb-5 transition-colors">
                    <Icon className="w-8 h-8 text-teamwork-blue group-hover:text-white transition-colors" />
                  </div>
                  <h3 className="text-xl font-bold mb-2 group-hover:text-teamwork-blue transition-colors">{service.title}</h3>
                  <p className="text-text-secondary mb-4">{service.description}</p>
                  <div className="flex items-center text-teamwork-blue font-semibold text-sm">
                    <span>Learn more</span>
                    <svg className="w-4 h-4 ml-1 group-hover:translate-x-1 transition-transform" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                    </svg>
                  </div>
                </Link>
              )
            })}
          </div>

          <div className="text-center mt-12">
            <Link href="/service-areas/" className="inline-flex items-center text-teamwork-blue hover:text-[#0094CC] font-semibold">
              View all service areas
              <svg className="w-5 h-5 ml-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
              </svg>
            </Link>
          </div>
        </div>
      </section>

      {/* Why Choose Us - Split Section with Image */}
      <section className="section-padding bg-light-bg">
        <div className="container-custom">
          <div className="grid lg:grid-cols-2 gap-16 items-center">
            {/* Content */}
            <div>
              <span className="text-teamwork-blue font-bold text-sm uppercase tracking-wider">The Teamwork Difference</span>
              <h2 className="heading-2 mt-3 mb-6">Why Kansas City Homeowners Choose Us</h2>
              <p className="text-xl text-text-secondary mb-10">
                We're not just roofing contractors—we're your partners in protecting what matters most.
              </p>

              <div className="space-y-6">
                <div className="flex items-start space-x-4">
                  <div className="w-14 h-14 rounded-xl bg-teamwork-blue flex items-center justify-center flex-shrink-0">
                    <FiCamera className="w-7 h-7 text-white" />
                  </div>
                  <div>
                    <h4 className="font-bold text-lg mb-2">Photo-Proof Transparency</h4>
                    <p className="text-text-secondary">Every inspection includes detailed photos. You see exactly what we see—no surprises, no guesswork.</p>
                  </div>
                </div>

                <div className="flex items-start space-x-4">
                  <div className="w-14 h-14 rounded-xl bg-teamwork-blue flex items-center justify-center flex-shrink-0">
                    <FiClock className="w-7 h-7 text-white" />
                  </div>
                  <div>
                    <h4 className="font-bold text-lg mb-2">Same-Week Inspections</h4>
                    <p className="text-text-secondary">Your time matters. We schedule and arrive within the same week you contact us—guaranteed.</p>
                  </div>
                </div>

                <div className="flex items-start space-x-4">
                  <div className="w-14 h-14 rounded-xl bg-teamwork-blue flex items-center justify-center flex-shrink-0">
                    <FiCheckCircle className="w-7 h-7 text-white" />
                  </div>
                  <div>
                    <h4 className="font-bold text-lg mb-2">Clean Site Guarantee</h4>
                    <p className="text-text-secondary">Tarps, magnetic sweeps, daily cleanup. We leave your property spotless—like we were never there.</p>
                  </div>
                </div>

                <div className="flex items-start space-x-4">
                  <div className="w-14 h-14 rounded-xl bg-teamwork-blue flex items-center justify-center flex-shrink-0">
                    <FiShield className="w-7 h-7 text-white" />
                  </div>
                  <div>
                    <h4 className="font-bold text-lg mb-2">Teamwork Warranty</h4>
                    <p className="text-text-secondary">Workmanship backed by our partnership commitment, plus manufacturer warranties on materials.</p>
                  </div>
                </div>
              </div>

              <div className="mt-10">
                <Link href="/about/" className="btn-primary inline-flex items-center">
                  Learn More About Us
                  <svg className="w-5 h-5 ml-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                  </svg>
                </Link>
              </div>
            </div>

            {/* Image Placeholder - Professional Photo */}
            <div className="relative h-[600px] rounded-2xl overflow-hidden shadow-2xl">
              <div className="absolute inset-0 bg-gradient-to-br from-gray-200 to-gray-300 flex items-center justify-center">
                <div className="text-center p-8">
                  <FiHome className="w-24 h-24 text-gray-400 mx-auto mb-4" />
                  <p className="text-gray-500 text-lg font-medium">Professional Team Photo</p>
                  <p className="text-gray-400 text-sm mt-2">or High-Quality Roof Installation Image</p>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Process Section - Horizontal Timeline */}
      <section className="section-padding bg-white">
        <div className="container-custom">
          <div className="text-center mb-16">
            <span className="text-teamwork-blue font-bold text-sm uppercase tracking-wider">How It Works</span>
            <h2 className="heading-2 mt-3 mb-4">The Teamwork Process</h2>
            <p className="text-xl text-text-secondary max-w-2xl mx-auto">
              Five simple steps from first contact to warranty activation
            </p>
          </div>

          <div className="grid md:grid-cols-5 gap-6">
            {processSteps.map((step, index) => {
              const Icon = step.icon
              return (
                <div key={index} className="text-center relative">
                  {/* Connection line */}
                  {index < processSteps.length - 1 && (
                    <div className="hidden md:block absolute top-12 left-1/2 w-full h-0.5 bg-light-border z-0"></div>
                  )}

                  {/* Step content */}
                  <div className="relative z-10">
                    <div className="w-24 h-24 rounded-full bg-teamwork-blue mx-auto mb-4 flex items-center justify-center shadow-lg">
                      <Icon className="w-10 h-10 text-white" />
                    </div>
                    <div className="w-8 h-8 rounded-full bg-teamwork-blue text-white font-bold flex items-center justify-center mx-auto mb-3 text-sm">
                      {index + 1}
                    </div>
                    <h4 className="font-bold mb-2 text-sm">{step.title}</h4>
                    <p className="text-xs text-text-secondary">{step.description}</p>
                  </div>
                </div>
              )
            })}
          </div>
        </div>
      </section>

      {/* Social Proof - Reviews */}
      <section className="section-padding bg-light-bg">
        <div className="container-custom">
          <div className="text-center mb-16">
            <span className="text-teamwork-blue font-bold text-sm uppercase tracking-wider">Customer Reviews</span>
            <h2 className="heading-2 mt-3 mb-4">What Kansas City Homeowners Say</h2>
            <p className="text-xl text-text-secondary">Real partnerships, real results</p>
          </div>

          <div className="grid md:grid-cols-3 gap-8 mb-12">
            {reviews.map((review, index) => (
              <div key={index} className="bg-white rounded-xl p-8 shadow-lg hover:shadow-xl transition-shadow">
                <div className="flex mb-4">
                  {[...Array(review.rating)].map((_, i) => (
                    <FiStar key={i} className="w-5 h-5 text-yellow-400 fill-current" />
                  ))}
                </div>
                <p className="text-text-secondary mb-6 text-lg italic">"{review.text}"</p>
                <div className="flex items-center space-x-3 pt-6 border-t border-light-border">
                  <div className="w-12 h-12 rounded-full bg-teamwork-blue/10 flex items-center justify-center font-bold text-teamwork-blue">
                    {review.name.charAt(0)}
                  </div>
                  <div>
                    <p className="font-bold">{review.name}</p>
                    <p className="text-sm text-text-secondary">{review.city}, KS</p>
                  </div>
                </div>
              </div>
            ))}
          </div>

          <div className="text-center">
            <Link href="/reviews/" className="btn-secondary inline-flex items-center">
              Read All Reviews
              <svg className="w-5 h-5 ml-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
              </svg>
            </Link>
          </div>
        </div>
      </section>

      <BrandsWeInstall variant="full" />

      <CTABand title="Ready to Protect Your Home?" subtitle="Same-week inspections available. Book online or call now." />
    </>
  )
}
