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
                <div key={index} className="group [perspective:1000px]">
                  <div className="relative w-full h-[340px] transition-transform duration-700 [transform-style:preserve-3d] group-hover:[transform:rotateY(180deg)]">
                    {/* Front */}
                    <div className="absolute inset-0 [backface-visibility:hidden]">
                      <div className="h-full card hover:border-teamwork-blue transition-colors flex flex-col">
                        <Icon className="w-12 h-12 text-teamwork-blue mb-4 group-hover:scale-110 transition-transform" />
                        <h3 className="heading-4 mb-3">{service.title}</h3>
                        <p className="text-text-secondary mb-4 flex-grow">{service.description}</p>
                        <ul className="space-y-2">
                          {service.features.map((feature, idx) => (
                            <li key={idx} className="flex items-center text-sm text-text-muted">
                              <span className="w-1.5 h-1.5 bg-teamwork-blue rounded-full mr-2"></span>
                              {feature}
                            </li>
                          ))}
                        </ul>
                        <p className="text-xs text-teamwork-blue font-medium mt-4">Hover for details →</p>
                      </div>
                    </div>
                    {/* Back */}
                    <div className="absolute inset-0 [backface-visibility:hidden] [transform:rotateY(180deg)]">
                      <div className="h-full bg-gradient-to-br from-teamwork-blue to-[#0094CC] text-white rounded-lg p-6 shadow-xl flex flex-col justify-between">
                        <div>
                          <Icon className="w-12 h-12 mb-4 opacity-90" />
                          <h3 className="text-xl font-bold mb-3">{service.title}</h3>
                          <p className="text-white/90 text-sm mb-4">{service.description}</p>
                          <div className="space-y-2 mb-6">
                            {service.features.map((feature, idx) => (
                              <div key={idx} className="flex items-center text-sm">
                                <span className="w-1.5 h-1.5 bg-white rounded-full mr-2"></span>
                                <span className="text-white/90">{feature}</span>
                              </div>
                            ))}
                          </div>
                        </div>
                        <Link
                          href={service.href}
                          className="block w-full text-center bg-white text-teamwork-blue py-3 rounded-lg font-semibold hover:bg-gray-100 transition-colors"
                        >
                          Learn More →
                        </Link>
                      </div>
                    </div>
                  </div>
                </div>
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
            <div className="group relative overflow-hidden card hover:border-teamwork-blue transition-all duration-300 hover:shadow-xl hover:-translate-y-1">
              <div className="absolute inset-0 bg-gradient-to-br from-teamwork-blue/5 to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-300"></div>
              <div className="relative z-10">
                <h3 className="heading-4 mb-3 group-hover:text-teamwork-blue transition-colors">Repair</h3>
                <p className="text-text-secondary mb-4">
                  Minor damage, isolated issues, or quick fixes
                </p>
                <Link href="/services/roof-repair/" className="inline-flex items-center text-teamwork-blue hover:underline font-medium">
                  Roof Repair →
                </Link>
              </div>
            </div>

            <div className="group relative overflow-hidden card hover:border-teamwork-blue transition-all duration-300 hover:shadow-xl hover:-translate-y-1">
              <div className="absolute inset-0 bg-gradient-to-br from-teamwork-blue/5 to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-300"></div>
              <div className="relative z-10">
                <h3 className="heading-4 mb-3 group-hover:text-teamwork-blue transition-colors">Replace</h3>
                <p className="text-text-secondary mb-4">
                  Age, widespread damage, or full upgrade
                </p>
                <Link href="/services/roof-replacement/" className="inline-flex items-center text-teamwork-blue hover:underline font-medium">
                  Roof Replacement →
                </Link>
              </div>
            </div>

            <div className="group relative overflow-hidden card hover:border-teamwork-blue transition-all duration-300 hover:shadow-xl hover:-translate-y-1">
              <div className="absolute inset-0 bg-gradient-to-br from-teamwork-blue/5 to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-300"></div>
              <div className="relative z-10">
                <h3 className="heading-4 mb-3 group-hover:text-teamwork-blue transition-colors">Storm Damage</h3>
                <p className="text-text-secondary mb-4">
                  Recent storm? We inspect roof, gutters, siding, and windows
                </p>
                <Link href="/storm/" className="inline-flex items-center text-teamwork-blue hover:underline font-medium">
                  Storm Help →
                </Link>
              </div>
            </div>
          </div>
        </div>
      </section>

      <CTABand />
    </>
  )
}
