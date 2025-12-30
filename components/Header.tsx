'use client'

import { useState } from 'react'
import Link from 'next/link'
import { FiMenu, FiX, FiPhone, FiChevronDown } from 'react-icons/fi'

export default function Header() {
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false)
  const [servicesDropdownOpen, setServicesDropdownOpen] = useState(false)

  return (
    <header className="sticky top-0 z-50 bg-dark-bg/95 backdrop-blur-sm border-b border-dark-border">
      <div className="container-custom">
        <div className="flex items-center justify-between h-20">
          {/* Logo */}
          <Link href="/" className="flex items-center space-x-2">
            <div className="text-2xl font-bold">
              <span className="text-teamwork-blue">TEAMWORK</span>
              <span className="text-white"> ROOFING</span>
            </div>
          </Link>

          {/* Desktop Navigation */}
          <nav className="hidden lg:flex items-center space-x-8">
            {/* Services Dropdown */}
            <div
              className="relative"
              onMouseEnter={() => setServicesDropdownOpen(true)}
              onMouseLeave={() => setServicesDropdownOpen(false)}
            >
              <button className="flex items-center space-x-1 text-gray-300 hover:text-white transition-colors">
                <span>Services</span>
                <FiChevronDown className="w-4 h-4" />
              </button>

              {servicesDropdownOpen && (
                <div className="absolute top-full left-0 mt-2 w-56 bg-dark-surface border border-dark-border rounded-lg shadow-xl py-2">
                  <Link href="/services/" className="block px-4 py-2 text-gray-300 hover:text-white hover:bg-dark-bg transition-colors">
                    All Services
                  </Link>
                  <Link href="/services/roof-replacement/" className="block px-4 py-2 text-gray-300 hover:text-white hover:bg-dark-bg transition-colors">
                    Roof Replacement
                  </Link>
                  <Link href="/services/roof-repair/" className="block px-4 py-2 text-gray-300 hover:text-white hover:bg-dark-bg transition-colors">
                    Roof Repair
                  </Link>
                  <Link href="/services/gutters/" className="block px-4 py-2 text-gray-300 hover:text-white hover:bg-dark-bg transition-colors">
                    Gutters
                  </Link>
                  <Link href="/services/siding/" className="block px-4 py-2 text-gray-300 hover:text-white hover:bg-dark-bg transition-colors">
                    Siding
                  </Link>
                  <Link href="/services/windows/" className="block px-4 py-2 text-gray-300 hover:text-white hover:bg-dark-bg transition-colors">
                    Windows
                  </Link>
                </div>
              )}
            </div>

            <Link href="/storm/" className="text-gray-300 hover:text-white transition-colors">
              Storm Damage
            </Link>
            <Link href="/financing/" className="text-gray-300 hover:text-white transition-colors">
              Financing
            </Link>
            <Link href="/projects/" className="text-gray-300 hover:text-white transition-colors">
              Projects
            </Link>
            <Link href="/reviews/" className="text-gray-300 hover:text-white transition-colors">
              Reviews
            </Link>
            <Link href="/faq/" className="text-gray-300 hover:text-white transition-colors">
              FAQ
            </Link>
            <Link href="/contact/" className="text-gray-300 hover:text-white transition-colors">
              Contact
            </Link>
          </nav>

          {/* Desktop CTAs */}
          <div className="hidden lg:flex items-center space-x-4">
            <a href="tel:9133963717" className="p-2 text-teamwork-blue hover:text-blue-400 transition-colors">
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
            className="lg:hidden p-2 text-white"
            onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
          >
            {mobileMenuOpen ? <FiX className="w-6 h-6" /> : <FiMenu className="w-6 h-6" />}
          </button>
        </div>

        {/* Mobile Menu */}
        {mobileMenuOpen && (
          <nav className="lg:hidden py-4 border-t border-dark-border">
            <div className="flex flex-col space-y-4">
              <Link href="/services/" className="text-gray-300 hover:text-white transition-colors">
                All Services
              </Link>
              <Link href="/services/roof-replacement/" className="text-gray-300 hover:text-white transition-colors pl-4">
                Roof Replacement
              </Link>
              <Link href="/services/roof-repair/" className="text-gray-300 hover:text-white transition-colors pl-4">
                Roof Repair
              </Link>
              <Link href="/services/gutters/" className="text-gray-300 hover:text-white transition-colors pl-4">
                Gutters
              </Link>
              <Link href="/services/siding/" className="text-gray-300 hover:text-white transition-colors pl-4">
                Siding
              </Link>
              <Link href="/services/windows/" className="text-gray-300 hover:text-white transition-colors pl-4">
                Windows
              </Link>
              <Link href="/storm/" className="text-gray-300 hover:text-white transition-colors">
                Storm Damage
              </Link>
              <Link href="/financing/" className="text-gray-300 hover:text-white transition-colors">
                Financing
              </Link>
              <Link href="/projects/" className="text-gray-300 hover:text-white transition-colors">
                Projects
              </Link>
              <Link href="/reviews/" className="text-gray-300 hover:text-white transition-colors">
                Reviews
              </Link>
              <Link href="/faq/" className="text-gray-300 hover:text-white transition-colors">
                FAQ
              </Link>
              <Link href="/contact/" className="text-gray-300 hover:text-white transition-colors">
                Contact
              </Link>
            </div>
          </nav>
        )}
      </div>

      {/* Service Area Line */}
      <div className="bg-dark-surface border-t border-dark-border">
        <div className="container-custom py-2">
          <p className="text-center text-sm text-gray-400">
            Serving Kansas City Metro — KCK, KCMO, Johnson County, Wyandotte, Jackson, and nearby areas
          </p>
        </div>
      </div>
    </header>
  )
}
