import Link from 'next/link'
import { FiHome, FiCloudRain, FiDroplet, FiLayers, FiSquare, FiCheckCircle, FiStar } from 'react-icons/fi'
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

  const projects = [
    { city: 'Overland Park', service: 'Roof Replacement', image: '/projects/placeholder.jpg' },
    { city: 'Lenexa', service: 'Storm Repair', image: '/projects/placeholder.jpg' },
    { city: 'Olathe', service: 'Gutters & Siding', image: '/projects/placeholder.jpg' },
    { city: 'Kansas City', service: 'Roof Repair', image: '/projects/placeholder.jpg' },
    { city: 'Shawnee', service: 'Full Exterior', image: '/projects/placeholder.jpg' },
    { city: 'Leawood', service: 'Roof Replacement', image: '/projects/placeholder.jpg' }
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

  const faqs = [
    {
      question: 'Do you really inspect same-week?',
      answer: 'Yes — it\'s our promise. We schedule inspections within the same week you contact us.'
    },
    {
      question: 'What does photo-proof inspection mean?',
      answer: 'We document everything with photos so you can see exactly what we see — full transparency.'
    },
    {
      question: 'What areas do you serve?',
      answer: 'Kansas City Metro including KCK, KCMO, Johnson County, Wyandotte, Jackson, and nearby areas.'
    },
    {
      question: 'Do you help with insurance claims?',
      answer: 'We provide photo documentation and scope details you can share with your insurer or adjuster. We do not negotiate claims or guarantee outcomes.'
    },
    {
      question: 'What financing options are available?',
      answer: 'We offer flexible Teamwork Financing options to fit your budget. Learn more on our Financing page.'
    },
    {
      question: 'What does the clean site guarantee include?',
      answer: 'We protect your property during work and ensure complete cleanup — your home, your peace of mind.'
    }
  ]

  return (
    <>
      {/* Hero Section */}
      <section className="relative bg-light-bg pt-20 pb-24">
        <div className="container-custom">
          <div className="grid lg:grid-cols-2 gap-12 items-center">
            <div>
              <h1 className="heading-1 mb-6">
                Roofing & Exteriors — Done{' '}
                <span className="text-teamwork-blue">The Teamwork Way</span>
              </h1>
              <p className="text-xl text-text-secondary mb-4">
                A partnership from day one. Same-week inspections, photo documentation, and clean site practices across Kansas City Metro.
              </p>

              <p className="text-sm text-text-secondary mb-8">
                <Link href="/service-areas/" className="hover:text-teamwork-blue hover:underline transition-colors">
                  Explore service areas →
                </Link>
              </p>

              <div className="flex flex-col sm:flex-row gap-4 mb-8">
                <Link href="/book/" className="btn-primary">
                  Book Same-Week Inspection
                </Link>
                <Link href="/estimate/" className="btn-secondary">
                  Start Teamwork Estimate
                </Link>
              </div>

              {/* Trust Snippets */}
              <div className="grid grid-cols-2 gap-4 pt-6 border-t border-light-border">
                <div className="flex items-start space-x-2">
                  <FiCheckCircle className="w-5 h-5 text-teamwork-blue mt-1 flex-shrink-0" />
                  <span className="text-sm text-text-secondary">Licensed & Insured</span>
                </div>
                <div className="flex items-start space-x-2">
                  <FiCheckCircle className="w-5 h-5 text-teamwork-blue mt-1 flex-shrink-0" />
                  <span className="text-sm text-text-secondary">Photo Documentation Included</span>
                </div>
                <div className="flex items-start space-x-2">
                  <FiCheckCircle className="w-5 h-5 text-teamwork-blue mt-1 flex-shrink-0" />
                  <span className="text-sm text-text-secondary">Clean Site Guarantee</span>
                </div>
                <div className="flex items-start space-x-2">
                  <FiCheckCircle className="w-5 h-5 text-teamwork-blue mt-1 flex-shrink-0" />
                  <span className="text-sm text-text-secondary">Teamwork Warranty Backed</span>
                </div>
              </div>
            </div>

            <div className="relative h-[400px] lg:h-[500px] rounded-2xl overflow-hidden bg-white border border-light-border">
              {/* Placeholder for hero image */}
              <div className="absolute inset-0 flex items-center justify-center text-text-muted">
                Hero Image: Modern home with new roof
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Service Tiles */}
      <section className="section-padding bg-light-bg">
        <div className="container-custom">
          <div className="text-center mb-12">
            <h2 className="heading-2 mb-4">Our Services</h2>
            <p className="text-xl text-text-secondary">Complete exterior solutions for your home</p>
          </div>

          <div className="grid md:grid-cols-2 lg:grid-cols-5 gap-6">
            {services.map((service, index) => {
              const Icon = service.icon
              return (
                <Link
                  key={index}
                  href={service.href}
                  className="card hover:border-teamwork-blue transition-all duration-200 group"
                >
                  <Icon className="w-12 h-12 text-teamwork-blue mb-4 group-hover:scale-110 transition-transform" />
                  <h3 className="text-xl font-semibold mb-2">{service.title}</h3>
                  <p className="text-text-secondary text-sm">{service.description}</p>
                </Link>
              )
            })}
          </div>
        </div>
      </section>

      {/* Partnership Promise Strip */}
      <PromiseStrip />

      {/* Projects Near You */}
      <section className="section-padding bg-light-bg">
        <div className="container-custom">
          <div className="text-center mb-12">
            <h2 className="heading-2 mb-4">Projects Near You</h2>
            <p className="text-xl text-text-secondary">See our work across Kansas City Metro</p>
          </div>

          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6 mb-8">
            {projects.map((project, index) => (
              <div key={index} className="card group cursor-pointer">
                <div className="relative h-48 bg-light-bg rounded-lg mb-4 overflow-hidden">
                  <div className="absolute inset-0 flex items-center justify-center text-text-muted">
                    Project Photo
                  </div>
                </div>
                <div className="flex justify-between items-start">
                  <div>
                    <h4 className="font-semibold mb-1">{project.service}</h4>
                    <p className="text-sm text-text-secondary">{project.city}, KS</p>
                  </div>
                  <span className="text-xs px-3 py-1 bg-teamwork-blue/10 text-teamwork-blue rounded-full">
                    {project.city}
                  </span>
                </div>
              </div>
            ))}
          </div>

          <div className="text-center">
            <Link href="/projects/" className="btn-secondary">
              View All Projects
            </Link>
          </div>
        </div>
      </section>

      {/* The Teamwork Process */}
      <section className="section-padding bg-white">
        <div className="container-custom">
          <div className="text-center mb-12">
            <h2 className="heading-2 mb-4">The Teamwork Process</h2>
            <p className="text-xl text-text-secondary">Five steps, five promises</p>
          </div>

          <div className="grid md:grid-cols-2 lg:grid-cols-5 gap-6">
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

      {/* Financing Teaser */}
      <section className="section-padding bg-light-bg">
        <div className="container-custom">
          <div className="card max-w-3xl mx-auto text-center">
            <h2 className="heading-3 mb-4">Teamwork Financing Options</h2>
            <p className="text-text-secondary mb-6">
              Flexible payment plans to make your roofing and exterior projects affordable
            </p>
            <Link href="/financing/" className="btn-primary">
              Learn About Financing
            </Link>
          </div>
        </div>
      </section>

      {/* Brands We Install */}
      <BrandsWeInstall variant="full" />

      {/* Reviews Highlights */}
      <section className="section-padding bg-white">
        <div className="container-custom">
          <div className="text-center mb-12">
            <h2 className="heading-2 mb-4">What Customers Say</h2>
            <p className="text-xl text-text-secondary">Real experiences from real partnerships</p>
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

      {/* FAQ Quick Hits */}
      <section className="section-padding bg-light-bg">
        <div className="container-custom">
          <div className="text-center mb-12">
            <h2 className="heading-2 mb-4">Quick Answers</h2>
            <p className="text-xl text-text-secondary">Common questions about working with us</p>
          </div>

          <div className="max-w-3xl mx-auto space-y-4 mb-8">
            {faqs.map((faq, index) => (
              <div key={index} className="card">
                <h4 className="font-semibold mb-2">{faq.question}</h4>
                <p className="text-text-secondary text-sm">{faq.answer}</p>
              </div>
            ))}
          </div>

          <div className="text-center">
            <Link href="/faq/" className="btn-secondary">
              View All FAQs
            </Link>
          </div>
        </div>
      </section>

      {/* Final CTA Band */}
      <CTABand />
    </>
  )
}
