'use client'

import { useState, useEffect } from 'react'
import Link from 'next/link'
import Image from 'next/image'
import { FiMenu, FiX, FiPhone, FiChevronDown, FiMapPin } from 'react-icons/fi'

export default function Header() {
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false)
  const [servicesDropdownOpen, setServicesDropdownOpen] = useState(false)
  const [scrolled, setScrolled] = useState(false)

  useEffect(() => {
    const handleScroll = () => {
      setScrolled(window.scrollY > 20)
    }
    window.addEventListener('scroll', handleScroll)
    return () => window.removeEventListener('scroll', handleScroll)
  }, [])

  return (
    <header className={`sticky top-0 z-50 transition-all duration-300 ${
      scrolled
        ? 'bg-white/98 backdrop-blur-md shadow-lg'
        : 'bg-white/95 backdrop-blur-sm shadow-sm'
    }`}>
      <div className="container-custom">
        <div className="flex items-center justify-between h-20 md:h-24">
          {/* Logo */}
          <Link href="/" className="flex items-center group">
            <Image
              src="/teamwork-logo.png"
              alt="Teamwork Roofing Services"
              width={250}
              height={194}
              className="h-14 md:h-16 w-auto transition-transform group-hover:scale-105"
              priority
            />
          </Link>

          {/* Desktop Navigation */}
          <nav className="hidden lg:flex items-center space-x-1">
            {/* Services Mega Menu */}
            <div
              className="relative"
              onMouseEnter={() => setServicesDropdownOpen(true)}
              onMouseLeave={() => setServicesDropdownOpen(false)}
            >
              <button className="flex items-center space-x-1 px-4 py-2 text-text-secondary hover:text-teamwork-blue transition-colors font-medium rounded-lg hover:bg-gray-50">
                <span>Services</span>
                <FiChevronDown className={`w-4 h-4 transition-transform ${servicesDropdownOpen ? 'rotate-180' : ''}`} />
              </button>

              {servicesDropdownOpen && (
                <div className="absolute top-full left-0 mt-2 w-72 bg-white border border-gray-200 rounded-xl shadow-2xl py-3 animate-in fade-in slide-in-from-top-2 duration-200">
                  <div className="px-4 py-2 border-b border-gray-100">
                    <p className="text-xs font-semibold text-gray-500 uppercase tracking-wider">Our Services</p>
                  </div>
                  <Link href="/services/" className="flex items-center px-4 py-3 text-text-secondary hover:text-teamwork-blue hover:bg-blue-50 transition-all group">
                    <div className="w-8 h-8 rounded-lg bg-teamwork-blue/10 flex items-center justify-center mr-3 group-hover:bg-teamwork-blue/20 transition-colors">
                      <span className="text-xs font-bold text-teamwork-blue">All</span>
                    </div>
                    <span className="font-medium">All Services</span>
                  </Link>
                  <Link href="/services/roof-replacement/" className="flex items-center px-4 py-3 text-text-secondary hover:text-teamwork-blue hover:bg-blue-50 transition-all">
                    <div className="w-2 h-2 rounded-full bg-teamwork-blue/40 mr-4"></div>
                    <span>Roof Replacement</span>
                  </Link>
                  <Link href="/services/roof-repair/" className="flex items-center px-4 py-3 text-text-secondary hover:text-teamwork-blue hover:bg-blue-50 transition-all">
                    <div className="w-2 h-2 rounded-full bg-teamwork-blue/40 mr-4"></div>
                    <span>Roof Repair</span>
                  </Link>
                  <Link href="/services/gutters/" className="flex items-center px-4 py-3 text-text-secondary hover:text-teamwork-blue hover:bg-blue-50 transition-all">
                    <div className="w-2 h-2 rounded-full bg-teamwork-blue/40 mr-4"></div>
                    <span>Gutters</span>
                  </Link>
                  <Link href="/services/siding/" className="flex items-center px-4 py-3 text-text-secondary hover:text-teamwork-blue hover:bg-blue-50 transition-all">
                    <div className="w-2 h-2 rounded-full bg-teamwork-blue/40 mr-4"></div>
                    <span>Siding</span>
                  </Link>
                  <Link href="/services/windows/" className="flex items-center px-4 py-3 text-text-secondary hover:text-teamwork-blue hover:bg-blue-50 transition-all">
                    <div className="w-2 h-2 rounded-full bg-teamwork-blue/40 mr-4"></div>
                    <span>Windows</span>
                  </Link>
                </div>
              )}
            </div>

            <Link href="/storm/" className="px-4 py-2 text-text-secondary hover:text-teamwork-blue transition-colors font-medium rounded-lg hover:bg-gray-50">
              Storm Damage
            </Link>
            <Link href="/projects/" className="px-4 py-2 text-text-secondary hover:text-teamwork-blue transition-colors font-medium rounded-lg hover:bg-gray-50">
              Projects
            </Link>
            <Link href="/reviews/" className="px-4 py-2 text-text-secondary hover:text-teamwork-blue transition-colors font-medium rounded-lg hover:bg-gray-50">
              Reviews
            </Link>
            <Link href="/service-areas/" className="px-4 py-2 text-text-secondary hover:text-teamwork-blue transition-colors font-medium rounded-lg hover:bg-gray-50 flex items-center gap-1">
              <FiMapPin className="w-4 h-4" />
              Areas
            </Link>
          </nav>

          {/* Desktop CTAs */}
          <div className="hidden lg:flex items-center gap-3">
            <a
              href="tel:9133963717"
              className="flex items-center gap-2 px-4 py-2.5 text-teamwork-blue hover:bg-blue-50 rounded-lg transition-all font-semibold group"
            >
              <div className="w-9 h-9 rounded-lg bg-teamwork-blue/10 flex items-center justify-center group-hover:bg-teamwork-blue/20 transition-colors">
                <FiPhone className="w-4 h-4" />
              </div>
              <span className="hidden xl:inline">(913) 396-3717</span>
            </a>
            <Link
              href="/book/"
              className="px-6 py-2.5 bg-teamwork-blue text-white font-semibold rounded-lg hover:bg-[#0094CC] transition-all shadow-md hover:shadow-lg transform hover:scale-[1.02]"
            >
              Book Inspection
            </Link>
          </div>

          {/* Mobile Menu Button */}
          <button
            className="lg:hidden p-2 text-text-primary hover:bg-gray-100 rounded-lg transition-colors"
            onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
          >
            {mobileMenuOpen ? <FiX className="w-6 h-6" /> : <FiMenu className="w-6 h-6" />}
          </button>
        </div>

        {/* Mobile Menu */}
        {mobileMenuOpen && (
          <nav className="lg:hidden py-6 border-t border-light-border animate-in slide-in-from-top duration-300">
            <div className="flex flex-col space-y-1">
              <Link href="/services/" className="px-4 py-3 text-text-secondary hover:text-teamwork-blue hover:bg-gray-50 rounded-lg transition-colors font-medium">
                All Services
              </Link>
              <Link href="/services/roof-replacement/" className="px-4 py-3 text-text-secondary hover:text-teamwork-blue hover:bg-gray-50 rounded-lg transition-colors pl-8">
                Roof Replacement
              </Link>
              <Link href="/services/roof-repair/" className="px-4 py-3 text-text-secondary hover:text-teamwork-blue hover:bg-gray-50 rounded-lg transition-colors pl-8">
                Roof Repair
              </Link>
              <Link href="/services/gutters/" className="px-4 py-3 text-text-secondary hover:text-teamwork-blue hover:bg-gray-50 rounded-lg transition-colors pl-8">
                Gutters
              </Link>
              <Link href="/services/siding/" className="px-4 py-3 text-text-secondary hover:text-teamwork-blue hover:bg-gray-50 rounded-lg transition-colors pl-8">
                Siding
              </Link>
              <Link href="/services/windows/" className="px-4 py-3 text-text-secondary hover:text-teamwork-blue hover:bg-gray-50 rounded-lg transition-colors pl-8">
                Windows
              </Link>
              <Link href="/storm/" className="px-4 py-3 text-text-secondary hover:text-teamwork-blue hover:bg-gray-50 rounded-lg transition-colors font-medium">
                Storm Damage
              </Link>
              <Link href="/projects/" className="px-4 py-3 text-text-secondary hover:text-teamwork-blue hover:bg-gray-50 rounded-lg transition-colors font-medium">
                Projects
              </Link>
              <Link href="/reviews/" className="px-4 py-3 text-text-secondary hover:text-teamwork-blue hover:bg-gray-50 rounded-lg transition-colors font-medium">
                Reviews
              </Link>
              <Link href="/service-areas/" className="px-4 py-3 text-text-secondary hover:text-teamwork-blue hover:bg-gray-50 rounded-lg transition-colors font-medium flex items-center gap-2">
                <FiMapPin className="w-4 h-4" />
                Service Areas
              </Link>
              <Link href="/contact/" className="px-4 py-3 text-text-secondary hover:text-teamwork-blue hover:bg-gray-50 rounded-lg transition-colors font-medium">
                Contact
              </Link>

              {/* Mobile CTAs */}
              <div className="pt-4 px-4 space-y-3 border-t border-gray-200 mt-4">
                <a
                  href="tel:9133963717"
                  className="flex items-center justify-center gap-2 px-6 py-3 bg-gray-100 text-teamwork-blue rounded-lg font-semibold hover:bg-gray-200 transition-colors"
                >
                  <FiPhone className="w-4 h-4" />
                  (913) 396-3717
                </a>
                <Link
                  href="/book/"
                  className="flex items-center justify-center px-6 py-3 bg-teamwork-blue text-white font-semibold rounded-lg hover:bg-[#0094CC] transition-colors"
                >
                  Book Inspection
                </Link>
              </div>
            </div>
          </nav>
        )}
      </div>

      {/* Service Area Line - Subtle and Modern */}
      <div className="bg-gradient-to-r from-gray-50 via-blue-50/30 to-gray-50 border-t border-gray-100">
        <div className="container-custom py-2.5">
          <p className="text-center text-xs text-text-muted flex items-center justify-center gap-2">
            <FiMapPin className="w-3.5 h-3.5 text-teamwork-blue" />
            <span>Serving Kansas City Metro — KCK, KCMO, Johnson County, and surrounding areas</span>
          </p>
        </div>
      </div>
    </header>
  )
}
