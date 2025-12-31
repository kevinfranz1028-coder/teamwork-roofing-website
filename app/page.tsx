import Link from 'next/link'
import { FiHome, FiCloudRain, FiDroplet, FiLayers, FiSquare, FiCheckCircle, FiStar, FiPhone, FiAward } from 'react-icons/fi'
import PromiseStrip from '@/components/PromiseStrip'
import CTABand from '@/components/CTABand'
import BrandsWeInstall from '@/components/BrandsWeInstall'

export default function Home() {
  const services = [
    {
      icon: FiHome,
      title: 'Roofing',
      description: 'Roof Replacement & Repair',
      href: '/services/roof-replacement/'
    },
    {
      icon: FiCloudRain,
      title: 'Storm Damage',
      description: 'Full exterior inspection & documentation',
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
      description: 'Protect and beautify',
      href: '/services/siding/'
    },
    {
      icon: FiSquare,
      title: 'Windows',
      description: 'Comfort and efficiency',
      href: '/services/windows/'
    }
  ]

  const processSteps = [
    {
      number: 1,
      title: 'Same-Week Inspection',
      description: 'We schedule and arrive fast — your time matters'
    },
    {
      number: 2,
      title: 'Photo Documentation',
      description: 'Every detail captured and shared with you'
    },
    {
      number: 3,
      title: 'Clear Options',
      description: 'No pressure, just honest choices and pricing'
    },
    {
      number: 4,
      title: 'Expert Installation',
      description: 'Professional work with clean site practices'
    },
    {
      number: 5,
      title: 'Teamwork Warranty',
      description: 'Backed by our partnership commitment'
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
      text: 'Same-week inspection promise delivered! Professional crew, clear communication, and beautiful results on our new gutters and siding.'
    }
  ]

  const stats = [
    { number: '1000+', label: 'Projects Completed' },
    { number: '15+', label: 'Years Experience' },
    { number: '100%', label: 'Satisfaction Rate' },
    { number: '24/7', label: 'Emergency Service' }
  ]

  return (
    <>
      {/* Hero Section - Full Width with Background Image Overlay */}
      <section className="relative min-h-[600px] md:min-h-[700px] flex items-center">
        {/* Background Image with Overlay */}
        <div className="absolute inset-0 bg-gradient-to-br from-gray-900/95 via-gray-900/90 to-gray-800/95 z-0">
          {/* Pattern overlay for texture */}
          <div className="absolute inset-0 opacity-10" style={{
            backgroundImage: `url("data:image/svg+xml,%3Csvg width='60' height='60' viewBox='0 0 60 60' xmlns='http://www.w3.org/2000/svg'%3E%3Cg fill='none' fill-rule='evenodd'%3E%3Cg fill='%23ffffff' fill-opacity='1'%3E%3Cpath d='M36 34v-4h-2v4h-4v2h4v4h2v-4h4v-2h-4zm0-30V0h-2v4h-4v2h4v4h2V6h4V4h-4zM6 34v-4H4v4H0v2h4v4h2v-4h4v-2H6zM6 4V0H4v4H0v2h4v4h2V6h4V4H6z'/%3E%3C/g%3E%3C/g%3E%3C/svg%3E")`
          }}></div>
        </div>

        {/* Content */}
        <div className="container-custom relative z-10 py-20">
          <div className="max-w-4xl">
            {/* Main Headline */}
            <h1 className="text-4xl md:text-5xl lg:text-6xl font-bold text-white mb-6 leading-tight">
              Roofing & Exteriors <span className="block text-teamwork-blue mt-2">The Teamwork Way</span>
            </h1>

            {/* Subheadline */}
            <p className="text-xl md:text-2xl text-gray-200 mb-8 max-w-2xl">
              A partnership from day one. Same-week inspections, photo documentation, and clean site practices across Kansas City Metro.
            </p>

            {/* CTAs */}
            <div className="flex flex-col sm:flex-row gap-4 mb-10">
              <Link href="/book/" className="inline-flex items-center justify-center px-8 py-4 bg-teamwork-blue text-white font-bold text-lg rounded-lg hover:bg-[#0094CC] transition-all shadow-xl hover:shadow-2xl transform hover:-translate-y-0.5">
                Book Same-Week Inspection
              </Link>
              <a href="tel:9133963717" className="inline-flex items-center justify-center px-8 py-4 bg-white text-teamwork-blue font-bold text-lg rounded-lg hover:bg-gray-100 transition-all shadow-xl">
                <FiPhone className="mr-2" />
                913-396-3717
              </a>
            </div>

            {/* Trust Badges */}
            <div className="flex flex-wrap gap-6 pt-6">
              <div className="flex items-center space-x-2 text-white">
                <FiCheckCircle className="w-6 h-6 text-teamwork-blue" />
                <span className="font-medium">Licensed & Insured</span>
              </div>
              <div className="flex items-center space-x-2 text-white">
                <FiCheckCircle className="w-6 h-6 text-teamwork-blue" />
                <span className="font-medium">Same-Week Inspections</span>
              </div>
              <div className="flex items-center space-x-2 text-white">
                <FiCheckCircle className="w-6 h-6 text-teamwork-blue" />
                <span className="font-medium">Photo Documentation</span>
              </div>
              <div className="flex items-center space-x-2 text-white">
                <FiCheckCircle className="w-6 h-6 text-teamwork-blue" />
                <span className="font-medium">Clean Site Guarantee</span>
              </div>
            </div>
          </div>
        </div>

        {/* Decorative Element */}
        <div className="absolute bottom-0 left-0 right-0 h-24 bg-gradient-to-t from-white to-transparent"></div>
      </section>

      {/* Stats Bar */}
      <section className="py-12 bg-white border-b border-light-border">
        <div className="container-custom">
          <div className="grid grid-cols-2 md:grid-cols-4 gap-8">
            {stats.map((stat, index) => (
              <div key={index} className="text-center">
                <div className="text-4xl md:text-5xl font-bold text-teamwork-blue mb-2">{stat.number}</div>
                <div className="text-sm md:text-base text-text-secondary font-medium">{stat.label}</div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Service Tiles */}
      <section className="section-padding bg-light-bg">
        <div className="container-custom">
          <div className="text-center mb-12">
            <h2 className="heading-2 mb-4">Our Services</h2>
            <p className="text-xl text-text-secondary max-w-2xl mx-auto">
              Complete exterior solutions for your Kansas City home
            </p>
          </div>

          <div className="grid md:grid-cols-2 lg:grid-cols-5 gap-6">
            {services.map((service, index) => {
              const Icon = service.icon
              return (
                <Link
                  key={index}
                  href={service.href}
                  className="card hover:border-teamwork-blue transition-all duration-200 group text-center"
                >
                  <Icon className="w-14 h-14 text-teamwork-blue mx-auto mb-4 group-hover:scale-110 transition-transform" />
                  <h3 className="text-xl font-semibold mb-2">{service.title}</h3>
                  <p className="text-sm text-text-secondary">{service.description}</p>
                </Link>
              )
            })}
          </div>

          <div className="text-center mt-10">
            <Link href="/service-areas/" className="text-teamwork-blue hover:underline font-medium">
              Explore service areas →
            </Link>
          </div>
        </div>
      </section>

      <PromiseStrip />

      {/* Why Choose Teamwork - Visual Section */}
      <section className="section-padding bg-white">
        <div className="container-custom">
          <div className="grid lg:grid-cols-2 gap-16 items-center">
            {/* Left: Content */}
            <div>
              <h2 className="heading-2 mb-6">Why Kansas City Homeowners Choose Teamwork</h2>
              <p className="text-xl text-text-secondary mb-8">
                We're not just another roofing contractor. We're your partners in protecting your home.
              </p>

              <div className="space-y-6">
                <div className="flex items-start space-x-4">
                  <div className="w-12 h-12 rounded-full bg-teamwork-blue/10 flex items-center justify-center flex-shrink-0">
                    <FiCheckCircle className="w-6 h-6 text-teamwork-blue" />
                  </div>
                  <div>
                    <h4 className="font-semibold text-lg mb-2">Photo-Proof Transparency</h4>
                    <p className="text-text-secondary">Every inspection includes detailed photos so you see exactly what we see. No surprises, no guesswork.</p>
                  </div>
                </div>

                <div className="flex items-start space-x-4">
                  <div className="w-12 h-12 rounded-full bg-teamwork-blue/10 flex items-center justify-center flex-shrink-0">
                    <FiCheckCircle className="w-6 h-6 text-teamwork-blue" />
                  </div>
                  <div>
                    <h4 className="font-semibold text-lg mb-2">Same-Week Response</h4>
                    <p className="text-text-secondary">Your time matters. We schedule inspections within the same week you contact us—guaranteed.</p>
                  </div>
                </div>

                <div className="flex items-start space-x-4">
                  <div className="w-12 h-12 rounded-full bg-teamwork-blue/10 flex items-center justify-center flex-shrink-0">
                    <FiCheckCircle className="w-6 h-6 text-teamwork-blue" />
                  </div>
                  <div>
                    <h4 className="font-semibold text-lg mb-2">Clean Site Guarantee</h4>
                    <p className="text-text-secondary">Tarps, magnetic sweeps, daily cleanup. We leave your property spotless—like we were never there.</p>
                  </div>
                </div>

                <div className="flex items-start space-x-4">
                  <div className="w-12 h-12 rounded-full bg-teamwork-blue/10 flex items-center justify-center flex-shrink-0">
                    <FiAward className="w-6 h-6 text-teamwork-blue" />
                  </div>
                  <div>
                    <h4 className="font-semibold text-lg mb-2">Teamwork Warranty</h4>
                    <p className="text-text-secondary">Our workmanship is backed by our partnership commitment, plus manufacturer warranties on materials.</p>
                  </div>
                </div>
              </div>

              <div className="mt-8">
                <Link href="/about/" className="btn-secondary">
                  Learn More About Us
                </Link>
              </div>
            </div>

            {/* Right: Image Placeholder */}
            <div className="relative h-[500px] rounded-2xl overflow-hidden bg-white border border-light-border shadow-lg">
              <div className="absolute inset-0 flex items-center justify-center text-text-muted">
                Image: Team working on roof / Happy homeowner
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* The Teamwork Process */}
      <section className="section-padding bg-light-bg">
        <div className="container-custom">
          <div className="text-center mb-12">
            <h2 className="heading-2 mb-4">The Teamwork Process</h2>
            <p className="text-xl text-text-secondary max-w-2xl mx-auto">Five steps, five promises</p>
          </div>

          <div className="grid md:grid-cols-5 gap-6">
            {processSteps.map((step, index) => (
              <div key={index} className="text-center">
                <div className="w-16 h-16 rounded-full bg-teamwork-blue/10 border-2 border-teamwork-blue flex items-center justify-center mx-auto mb-4">
                  <span className="text-2xl font-bold text-teamwork-blue">{step.number}</span>
                </div>
                <h4 className="font-semibold mb-2">{step.title}</h4>
                <p className="text-sm text-text-secondary">{step.description}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Reviews */}
      <section className="section-padding bg-white">
        <div className="container-custom">
          <div className="text-center mb-12">
            <h2 className="heading-2 mb-4">What Kansas City Homeowners Say</h2>
            <p className="text-xl text-text-secondary">Real feedback from real partnerships</p>
          </div>

          <div className="grid md:grid-cols-3 gap-6 mb-8">
            {reviews.map((review, index) => (
              <div key={index} className="card">
                <div className="flex mb-3">
                  {[...Array(review.rating)].map((_, i) => (
                    <FiStar key={i} className="w-5 h-5 text-yellow-500 fill-current" />
                  ))}
                </div>
                <p className="text-text-secondary mb-4">{review.text}</p>
                <div className="border-t border-light-border pt-4">
                  <p className="font-semibold">{review.name}</p>
                  <p className="text-sm text-text-secondary">{review.city}, KS</p>
                </div>
              </div>
            ))}
          </div>

          <div className="text-center">
            <Link href="/reviews/" className="btn-secondary">
              Read All Reviews
            </Link>
          </div>
        </div>
      </section>

      <BrandsWeInstall variant="full" />

      <CTABand title="Ready to Get Started?" subtitle="Book your same-week inspection or get a quick estimate today" />
    </>
  )
}
