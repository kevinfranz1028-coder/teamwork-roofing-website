import Link from 'next/link'
import { FiHome, FiDroplet, FiLayers, FiSquare, FiTool, FiRefreshCw } from 'react-icons/fi'
import PromiseStrip from '@/components/PromiseStrip'
import CTABand from '@/components/CTABand'

export const metadata = {
  title: 'Roofing & Exterior Services | Teamwork Roofing Kansas City',
  description: 'Complete roofing and exterior services: roof replacement, repair, gutters, siding, and windows for Kansas City Metro homes.',
}

export default function ServicesPage() {
  const services = [
    {
      icon: FiRefreshCw,
      title: 'Roof Replacement',
      description: 'Complete roof replacement with premium materials and expert installation',
      features: ['Material options', 'Photo documentation', 'Clean site guarantee'],
      href: '/services/roof-replacement/'
    },
    {
      icon: FiTool,
      title: 'Roof Repair',
      description: 'Fast, professional repairs with honest repair vs replace guidance',
      features: ['Same-week service', 'Emergency response', 'Warranty backed'],
      href: '/services/roof-repair/'
    },
    {
      icon: FiDroplet,
      title: 'Gutters',
      description: 'Seamless gutters, gutter guards, and professional repair',
      features: ['Seamless installation', 'Guard options', 'Color matching'],
      href: '/services/gutters/'
    },
    {
      icon: FiLayers,
      title: 'Siding',
      description: 'Siding installation and repair to protect and beautify your home',
      features: ['Multiple materials', 'Insulation options', 'Color selection'],
      href: '/services/siding/'
    },
    {
      icon: FiSquare,
      title: 'Windows',
      description: 'Energy-efficient window replacement for comfort and savings',
      features: ['Energy efficiency', 'Professional install', 'Multiple styles'],
      href: '/services/windows/'
    }
  ]

  return (
    <>
      <section className="section-padding bg-light-bg">
        <div className="container-custom">
          <div className="text-center mb-16">
            <h1 className="heading-1 mb-6">Exterior Services Built on Teamwork</h1>
            <p className="text-xl text-text-secondary max-w-3xl mx-auto">
              From roofing to windows, every service backed by our five promises: warranty, same-week inspection, clean sites, photo documentation, and flexible financing
            </p>
          </div>

          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-8 mb-16">
            {services.map((service, index) => {
              const Icon = service.icon
              return (
                <Link
                  key={index}
                  href={service.href}
                  className="card hover:border-teamwork-blue transition-all duration-200 group"
                >
                  <Icon className="w-12 h-12 text-teamwork-blue mb-4 group-hover:scale-110 transition-transform" />
                  <h3 className="heading-4 mb-3">{service.title}</h3>
                  <p className="text-text-secondary mb-4">{service.description}</p>
                  <ul className="space-y-2">
                    {service.features.map((feature, idx) => (
                      <li key={idx} className="flex items-center text-sm text-text-muted">
                        <span className="w-1.5 h-1.5 bg-teamwork-blue rounded-full mr-2"></span>
                        {feature}
                      </li>
                    ))}
                  </ul>
                </Link>
              )
            })}
          </div>
        </div>
      </section>

      <PromiseStrip />

      {/* Which Service Fits You */}
      <section className="section-padding bg-white">
        <div className="container-custom">
          <div className="text-center mb-12">
            <h2 className="heading-2 mb-4">Which Service Fits You?</h2>
            <p className="text-xl text-text-secondary">Let us help you figure out what you need</p>
          </div>

          <div className="grid md:grid-cols-3 gap-8">
            <div className="card">
              <h3 className="heading-4 mb-3">Repair</h3>
              <p className="text-text-secondary mb-4">
                Minor damage, isolated issues, or quick fixes
              </p>
              <Link href="/services/roof-repair/" className="text-teamwork-blue hover:underline">
                Roof Repair →
              </Link>
            </div>

            <div className="card">
              <h3 className="heading-4 mb-3">Replace</h3>
              <p className="text-text-secondary mb-4">
                Age, widespread damage, or full upgrade
              </p>
              <Link href="/services/roof-replacement/" className="text-teamwork-blue hover:underline">
                Roof Replacement →
              </Link>
            </div>

            <div className="card">
              <h3 className="heading-4 mb-3">Storm Damage</h3>
              <p className="text-text-secondary mb-4">
                Recent storm? We inspect roof, gutters, siding, and windows
              </p>
              <Link href="/storm/" className="text-teamwork-blue hover:underline">
                Storm Help →
              </Link>
            </div>
          </div>
        </div>
      </section>

      <CTABand />
    </>
  )
}
