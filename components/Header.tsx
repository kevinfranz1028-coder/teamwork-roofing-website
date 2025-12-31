'use client'

import { useState } from 'react'
import Link from 'next/link'
import Image from 'next/image'
import { FiMenu, FiX, FiPhone, FiChevronDown } from 'react-icons/fi'

export default function Header() {
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false)
  const [servicesDropdownOpen, setServicesDropdownOpen] = useState(false)

  return (
    <header className="sticky top-0 z-50 bg-white/95 backdrop-blur-sm border-b border-light-border shadow-sm">
      <div className="container-custom">
        <div className="flex items-center justify-between h-20">
          {/* Logo */}
          <Link href="/" className="flex items-center space-x-3">
            <Image
              src="/teamwork-logo.png"
              alt="Teamwork Roofing Services"
              width={180}
              height={60}
              className="h-12 w-auto"
              priority
            />
          </Link>

          {/* Desktop Navigation */}
          <nav className="hidden lg:flex items-center space-x-8">
            {/* Services Dropdown */}
            <div
              className="relative"
              onMouseEnter={() => setServicesDropdownOpen(true)}
              onMouseLeave={() => setServicesDropdownOpen(false)}
            >
              <button className="flex items-center space-x-1 text-text-secondary hover:text-teamwork-blue transition-colors font-medium">
                <span>Services</span>
                <FiChevronDown className="w-4 h-4" />
              </button>

              {servicesDropdownOpen && (
                <div className="absolute top-full left-0 mt-2 w-56 bg-white border border-light-border rounded-lg shadow-lg py-2">
                  <Link href="/services/" className="block px-4 py-2 text-text-secondary hover:text-teamwork-blue hover:bg-light-surface transition-colors">
                    All Services
                  </Link>
                  <Link href="/services/roof-replacement/" className="block px-4 py-2 text-text-secondary hover:text-teamwork-blue hover:bg-light-surface transition-colors">
                    Roof Replacement
                  </Link>
                  <Link href="/services/roof-repair/" className="block px-4 py-2 text-text-secondary hover:text-teamwork-blue hover:bg-light-surface transition-colors">
                    Roof Repair
                  </Link>
                  <Link href="/services/gutters/" className="block px-4 py-2 text-text-secondary hover:text-teamwork-blue hover:bg-light-surface transition-colors">
                    Gutters
                  </Link>
                  <Link href="/services/siding/" className="block px-4 py-2 text-text-secondary hover:text-teamwork-blue hover:bg-light-surface transition-colors">
                    Siding
                  </Link>
                  <Link href="/services/windows/" className="block px-4 py-2 text-text-secondary hover:text-teamwork-blue hover:bg-light-surface transition-colors">
                    Windows
                  </Link>
                </div>
              )}
            </div>

            <Link href="/storm/" className="text-text-secondary hover:text-teamwork-blue transition-colors font-medium">
              Storm Damage
            </Link>
            <Link href="/financing/" className="text-text-secondary hover:text-teamwork-blue transition-colors font-medium">
              Financing
            </Link>
            <Link href="/projects/" className="text-text-secondary hover:text-teamwork-blue transition-colors font-medium">
              Projects
            </Link>
            <Link href="/reviews/" className="text-text-secondary hover:text-teamwork-blue transition-colors font-medium">
              Reviews
            </Link>
            <Link href="/faq/" className="text-text-secondary hover:text-teamwork-blue transition-colors font-medium">
              FAQ
            </Link>
            <Link href="/contact/" className="text-text-secondary hover:text-teamwork-blue transition-colors font-medium">
              Contact
            </Link>
          </nav>

          {/* Desktop CTAs */}
          <div className="hidden lg:flex items-center space-x-4">
            <a href="tel:9133963717" className="p-2 text-teamwork-blue hover:text-[#0094CC] transition-colors">
              <FiPhone className="w-5 h-5" />
            </a>
            <Link href="/estimate/" className="btn-secondary text-sm">
              Start Teamwork Estimate
            </Link>
            <Link href="/book/" className="btn-primary text-sm">
              Book Same-Week Inspection
            </Link>
          </div>

          {/* Mobile Menu Button */}
          <button
            className="lg:hidden p-2 text-text-primary"
            onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
          >
            {mobileMenuOpen ? <FiX className="w-6 h-6" /> : <FiMenu className="w-6 h-6" />}
          </button>
        </div>

        {/* Mobile Menu */}
        {mobileMenuOpen && (
          <nav className="lg:hidden py-4 border-t border-light-border">
            <div className="flex flex-col space-y-4">
              <Link href="/services/" className="text-text-secondary hover:text-teamwork-blue transition-colors">
                All Services
              </Link>
              <Link href="/services/roof-replacement/" className="text-text-secondary hover:text-teamwork-blue transition-colors pl-4">
                Roof Replacement
              </Link>
              <Link href="/services/roof-repair/" className="text-text-secondary hover:text-teamwork-blue transition-colors pl-4">
                Roof Repair
              </Link>
              <Link href="/services/gutters/" className="text-text-secondary hover:text-teamwork-blue transition-colors pl-4">
                Gutters
              </Link>
              <Link href="/services/siding/" className="text-text-secondary hover:text-teamwork-blue transition-colors pl-4">
                Siding
              </Link>
              <Link href="/services/windows/" className="text-text-secondary hover:text-teamwork-blue transition-colors pl-4">
                Windows
              </Link>
              <Link href="/storm/" className="text-text-secondary hover:text-teamwork-blue transition-colors">
                Storm Damage
              </Link>
              <Link href="/financing/" className="text-text-secondary hover:text-teamwork-blue transition-colors">
                Financing
              </Link>
              <Link href="/projects/" className="text-text-secondary hover:text-teamwork-blue transition-colors">
                Projects
              </Link>
              <Link href="/reviews/" className="text-text-secondary hover:text-teamwork-blue transition-colors">
                Reviews
              </Link>
              <Link href="/faq/" className="text-text-secondary hover:text-teamwork-blue transition-colors">
                FAQ
              </Link>
              <Link href="/contact/" className="text-text-secondary hover:text-teamwork-blue transition-colors">
                Contact
              </Link>
            </div>
          </nav>
        )}
      </div>

      {/* Service Area Line */}
      <div className="bg-light-surface border-t border-light-border">
        <div className="container-custom py-2">
          <p className="text-center text-sm text-text-muted">
            Serving Kansas City Metro — KCK, KCMO, Johnson County, Wyandotte, Jackson, and nearby areas
          </p>
        </div>
      </div>
    </header>
  )
}
