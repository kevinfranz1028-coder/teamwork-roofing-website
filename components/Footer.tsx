import Link from 'next/link'
import Image from 'next/image'
import { FiFacebook, FiInstagram, FiLinkedin } from 'react-icons/fi'

export default function Footer() {
  return (
    <footer className="bg-light-surface border-t border-light-border">
      <div className="container-custom section-padding">
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-12">
          {/* Company Info */}
          <div>
            <Link href="/" className="inline-block mb-4">
              <Image
                src="/teamwork-logo.png"
                alt="Teamwork Roofing Services"
                width={250}
                height={194}
                className="h-14 w-auto"
              />
            </Link>
            <p className="text-text-secondary mb-4">
              Roofing & Exteriors — Done The Teamwork Way
            </p>
            <div className="space-y-2 text-text-secondary">
              <p>Kansas City Metro Area</p>
              <p>
                <a href="tel:9133963717" className="hover:text-teamwork-blue transition-colors">
                  913-396-3717
                </a>
              </p>
            </div>
            <div className="flex space-x-4 mt-4">
              <a href="#" className="text-text-secondary hover:text-teamwork-blue transition-colors">
                <FiFacebook className="w-5 h-5" />
              </a>
              <a href="#" className="text-text-secondary hover:text-teamwork-blue transition-colors">
                <FiInstagram className="w-5 h-5" />
              </a>
              <a href="#" className="text-text-secondary hover:text-teamwork-blue transition-colors">
                <FiLinkedin className="w-5 h-5" />
              </a>
            </div>
          </div>

          {/* Services */}
          <div>
            <h4 className="font-semibold mb-4">Services</h4>
            <ul className="space-y-2">
              <li>
                <Link href="/services/roof-replacement/" className="text-text-secondary hover:text-teamwork-blue transition-colors">
                  Roof Replacement
                </Link>
              </li>
              <li>
                <Link href="/services/roof-repair/" className="text-text-secondary hover:text-teamwork-blue transition-colors">
                  Roof Repair
                </Link>
              </li>
              <li>
                <Link href="/services/gutters/" className="text-text-secondary hover:text-teamwork-blue transition-colors">
                  Gutters
                </Link>
              </li>
              <li>
                <Link href="/services/siding/" className="text-text-secondary hover:text-teamwork-blue transition-colors">
                  Siding
                </Link>
              </li>
              <li>
                <Link href="/services/windows/" className="text-text-secondary hover:text-teamwork-blue transition-colors">
                  Windows
                </Link>
              </li>
              <li>
                <Link href="/storm/" className="text-text-secondary hover:text-teamwork-blue transition-colors">
                  Storm Damage Inspection
                </Link>
              </li>
            </ul>
          </div>

          {/* Company */}
          <div>
            <h4 className="font-semibold mb-4">Company</h4>
            <ul className="space-y-2">
              <li>
                <Link href="/about/" className="text-text-secondary hover:text-teamwork-blue transition-colors">
                  About Us
                </Link>
              </li>
              <li>
                <Link href="/projects/" className="text-text-secondary hover:text-teamwork-blue transition-colors">
                  Projects
                </Link>
              </li>
              <li>
                <Link href="/reviews/" className="text-text-secondary hover:text-teamwork-blue transition-colors">
                  Reviews
                </Link>
              </li>
              <li>
                <Link href="/materials/" className="text-text-secondary hover:text-teamwork-blue transition-colors">
                  Materials & Brands
                </Link>
              </li>
              <li>
                <Link href="/financing/" className="text-text-secondary hover:text-teamwork-blue transition-colors">
                  Financing
                </Link>
              </li>
              <li>
                <Link href="/warranty/" className="text-text-secondary hover:text-teamwork-blue transition-colors">
                  Warranty
                </Link>
              </li>
              <li>
                <Link href="/faq/" className="text-text-secondary hover:text-teamwork-blue transition-colors">
                  FAQ
                </Link>
              </li>
            </ul>
          </div>

          {/* Get Started */}
          <div>
            <h4 className="font-semibold mb-4">Get Started</h4>
            <ul className="space-y-2">
              <li>
                <Link href="/book/" className="text-text-secondary hover:text-teamwork-blue transition-colors">
                  Book Same-Week Inspection
                </Link>
              </li>
              <li>
                <Link href="/estimate/" className="text-text-secondary hover:text-teamwork-blue transition-colors">
                  Start Teamwork Estimate
                </Link>
              </li>
              <li>
                <Link href="/contact/" className="text-text-secondary hover:text-teamwork-blue transition-colors">
                  Contact Us
                </Link>
              </li>
            </ul>
          </div>

          {/* Service Areas */}
          <div>
            <h4 className="font-semibold mb-4">Service Areas</h4>
            <ul className="space-y-2">
              <li>
                <Link href="/overland-park-ks/" className="text-text-secondary hover:text-teamwork-blue transition-colors">
                  Overland Park
                </Link>
              </li>
              <li>
                <Link href="/leawood-ks/" className="text-text-secondary hover:text-teamwork-blue transition-colors">
                  Leawood
                </Link>
              </li>
              <li>
                <Link href="/lenexa-ks/" className="text-text-secondary hover:text-teamwork-blue transition-colors">
                  Lenexa
                </Link>
              </li>
              <li className="mt-3">
                <Link href="/service-areas/" className="text-teamwork-blue hover:text-[#0094CC] transition-colors font-medium">
                  View All Areas →
                </Link>
              </li>
            </ul>
            <div className="mt-6">
              <p className="text-xs text-text-muted">
                Serving the full Kansas City Metro — KCK, KCMO, Johnson County, and nearby areas
              </p>
            </div>
          </div>
        </div>

        {/* Bottom Bar */}
        <div className="mt-12 pt-8 border-t border-light-border">
          <div className="flex flex-col md:flex-row justify-between items-center space-y-4 md:space-y-0">
            <p className="text-sm text-text-muted">
              &copy; {new Date().getFullYear()} Teamwork Roofing Services LLC. All rights reserved.
            </p>
            <div className="flex space-x-6 text-sm">
              <Link href="/privacy/" className="text-text-muted hover:text-teamwork-blue transition-colors">
                Privacy Policy
              </Link>
              <Link href="/terms/" className="text-text-muted hover:text-teamwork-blue transition-colors">
                Terms of Service
              </Link>
            </div>
          </div>
        </div>
      </div>
    </footer>
  )
}
