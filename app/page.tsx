import Link from 'next/link'
import Image from 'next/image'
import { FiHome, FiCloudRain, FiDroplet, FiLayers, FiSquare, FiCheckCircle, FiStar, FiPhone, FiAward, FiShield, FiClock, FiCamera, FiArrowRight, FiTool, FiUsers } from 'react-icons/fi'
import PromiseStrip from '@/components/PromiseStrip'
import CTABand from '@/components/CTABand'
import BrandsWeInstall from '@/components/BrandsWeInstall'

export default function Home() {
  const services = [
    {
      icon: FiHome,
      title: 'Roof Replacement',
      description: 'Complete roof systems with premium materials and expert installation',
      href: '/services/roof-replacement/'
    },
    {
      icon: FiTool,
      title: 'Roof Repair',
      description: 'Fast, reliable repairs that extend your roof\'s life',
      href: '/services/roof-repair/'
    },
    {
      icon: FiCloudRain,
      title: 'Storm Damage',
      description: 'Thorough inspection and insurance claim assistance',
      href: '/storm/'
    },
    {
      icon: FiDroplet,
      title: 'Gutters',
      description: 'Seamless gutters, gutter guards, and repair',
      href: '/services/gutters/'
    },
    {
      icon: FiLayers,
      title: 'Siding',
      description: 'Beautiful, durable siding that protects your home',
      href: '/services/siding/'
    },
    {
      icon: FiSquare,
      title: 'Windows',
      description: 'Energy-efficient window replacements',
      href: '/services/windows/'
    }
  ]

  const whyChoose = [
    {
      icon: FiCamera,
      title: 'Photo Documentation',
      description: 'Every inspection includes detailed photos so you see exactly what we see'
    },
    {
      icon: FiClock,
      title: 'Same-Week Service',
      description: 'We schedule and arrive within the same week you contact us'
    },
    {
      icon: FiCheckCircle,
      title: 'Clean Site Guarantee',
      description: 'Tarps, magnetic sweeps, daily cleanup—your property stays pristine'
    },
    {
      icon: FiShield,
      title: 'Warranty Protection',
      description: 'Workmanship warranty plus manufacturer coverage on all materials'
    }
  ]

  const stats = [
    { number: '1000+', label: 'Projects Completed' },
    { number: '15+', label: 'Years Experience' },
    { number: '4.9', label: 'Star Rating' },
    { number: '100%', label: 'Satisfaction Rate' }
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
      {/* Hero Section - Modern Professional Design */}
      <section className="relative bg-gradient-to-br from-gray-900 via-gray-800 to-gray-900 text-white overflow-hidden">
        {/* Background Pattern */}
        <div className="absolute inset-0 opacity-10">
          <div className="absolute inset-0" style={{
            backgroundImage: `url("data:image/svg+xml,%3Csvg width='60' height='60' viewBox='0 0 60 60' xmlns='http://www.w3.org/2000/svg'%3E%3Cg fill='none' fill-rule='evenodd'%3E%3Cg fill='%23ffffff' fill-opacity='0.4'%3E%3Cpath d='M36 34v-4h-2v4h-4v2h4v4h2v-4h4v-2h-4zm0-30V0h-2v4h-4v2h4v4h2V6h4V4h-4zM6 34v-4H4v4H0v2h4v4h2v-4h4v-2H6zM6 4V0H4v4H0v2h4v4h2V6h4V4H6z'/%3E%3C/g%3E%3C/g%3E%3C/svg%3E")`
          }}></div>
        </div>

        <div className="container-custom relative">
          <div className="py-20 md:py-28 lg:py-32">
            {/* Trust Badge */}
            <div className="inline-flex items-center gap-2 bg-white/10 backdrop-blur-md px-4 py-2 rounded-full mb-6 border border-white/20">
              <FiShield className="w-4 h-4 text-teamwork-blue" />
              <span className="text-sm font-semibold">Kansas City's Trusted Roofing Partner Since 2009</span>
            </div>

            {/* Main Headline */}
            <div className="max-w-4xl">
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

              {/* Stats Bar */}
              <div className="grid grid-cols-2 md:grid-cols-4 gap-6 pt-8 border-t border-white/20">
                {stats.map((stat, index) => (
                  <div key={index}>
                    <div className="text-3xl font-bold text-teamwork-blue mb-1">{stat.number}</div>
                    <div className="text-sm text-gray-400">{stat.label}</div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Services Grid */}
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
                <Link
                  key={index}
                  href={service.href}
                  className="group bg-white border border-gray-200 rounded-lg p-6 hover:border-teamwork-blue hover:shadow-lg transition-all"
                >
                  <div className="w-12 h-12 rounded-lg bg-gray-100 group-hover:bg-teamwork-blue flex items-center justify-center mb-4 transition-colors">
                    <Icon className="w-6 h-6 text-gray-600 group-hover:text-white transition-colors" />
                  </div>
                  <h3 className="text-lg font-semibold mb-2">{service.title}</h3>
                  <p className="text-text-secondary text-sm mb-4 leading-relaxed">{service.description}</p>
                  <div className="flex items-center text-teamwork-blue text-sm font-medium">
                    Learn more <FiArrowRight className="ml-1 w-4 h-4 group-hover:translate-x-1 transition-transform" />
                  </div>
                </Link>
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

      {/* Why Choose Us */}
      <section className="section-padding bg-gray-50">
        <div className="container-custom">
          <div className="max-w-3xl mx-auto text-center mb-16">
            <h2 className="heading-2 mb-4">The Teamwork Difference</h2>
            <p className="text-lg text-text-secondary">
              We're not just roofing contractors — we're your partners in protecting what matters most.
            </p>
          </div>

          <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-8 max-w-6xl mx-auto">
            {whyChoose.map((item, index) => {
              const Icon = item.icon
              return (
                <div key={index} className="text-center">
                  <div className="w-16 h-16 rounded-full bg-teamwork-blue mx-auto mb-4 flex items-center justify-center">
                    <Icon className="w-8 h-8 text-white" />
                  </div>
                  <h3 className="font-semibold text-lg mb-2">{item.title}</h3>
                  <p className="text-text-secondary text-sm leading-relaxed">{item.description}</p>
                </div>
              )
            })}
          </div>

          <div className="text-center mt-12">
            <Link href="/about/" className="inline-flex items-center btn-secondary">
              Learn More About Us <FiArrowRight className="ml-2 w-5 h-5" />
            </Link>
          </div>
        </div>
      </section>

      {/* Process Section */}
      <section className="section-padding bg-white">
        <div className="container-custom">
          <div className="max-w-3xl mx-auto text-center mb-16">
            <h2 className="heading-2 mb-4">How It Works</h2>
            <p className="text-lg text-text-secondary">
              From first contact to warranty activation, we make the process simple and transparent.
            </p>
          </div>

          <div className="max-w-4xl mx-auto">
            <div className="space-y-6">
              {[
                { step: '01', icon: FiPhone, title: 'Contact Us', desc: 'Call, text, or book online — same-day response guaranteed' },
                { step: '02', icon: FiClock, title: 'Same-Week Inspection', desc: 'We arrive within the week with all necessary equipment' },
                { step: '03', icon: FiCamera, title: 'Photo Documentation', desc: 'Detailed photos and clear explanation of findings' },
                { step: '04', icon: FiCheckCircle, title: 'Transparent Pricing', desc: 'Honest options with no pressure or hidden fees' },
                { step: '05', icon: FiShield, title: 'Expert Installation', desc: 'Professional work with clean site guarantee and warranty' }
              ].map((process, index) => {
                const Icon = process.icon
                return (
                  <div key={index} className="flex gap-6 items-start">
                    <div className="flex-shrink-0">
                      <div className="w-14 h-14 rounded-lg bg-teamwork-blue text-white flex items-center justify-center">
                        <Icon className="w-7 h-7" />
                      </div>
                    </div>
                    <div className="flex-1 pt-2">
                      <div className="flex items-baseline gap-3 mb-2">
                        <span className="text-xs font-bold text-teamwork-blue tracking-wider">{process.step}</span>
                        <h3 className="font-semibold text-lg">{process.title}</h3>
                      </div>
                      <p className="text-text-secondary leading-relaxed">{process.desc}</p>
                    </div>
                  </div>
                )
              })}
            </div>
          </div>
        </div>
      </section>

      {/* Reviews */}
      <section className="section-padding bg-gray-50">
        <div className="container-custom">
          <div className="max-w-3xl mx-auto text-center mb-16">
            <h2 className="heading-2 mb-4">What Kansas City Homeowners Say</h2>
            <p className="text-lg text-text-secondary">Real partnerships, real results</p>
          </div>

          <div className="grid md:grid-cols-3 gap-8 max-w-6xl mx-auto">
            {reviews.map((review, index) => (
              <div key={index} className="bg-white rounded-lg p-6 shadow-md">
                <div className="flex gap-1 mb-4">
                  {[...Array(review.rating)].map((_, i) => (
                    <FiStar key={i} className="w-5 h-5 text-yellow-400 fill-current" />
                  ))}
                </div>
                <p className="text-text-secondary mb-6 leading-relaxed">"{review.text}"</p>
                <div className="flex items-center gap-3 pt-4 border-t border-gray-200">
                  <div className="w-10 h-10 rounded-full bg-teamwork-blue/10 flex items-center justify-center font-semibold text-teamwork-blue">
                    {review.name.charAt(0)}
                  </div>
                  <div>
                    <div className="font-semibold text-sm">{review.name}</div>
                    <div className="text-xs text-text-secondary">{review.city}, KS</div>
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
