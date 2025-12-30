import Link from 'next/link'
import { FiHome, FiTool, FiPhone } from 'react-icons/fi'

export default function NotFound() {
  return (
    <section className="section-padding bg-dark-bg min-h-screen flex items-center justify-center">
      <div className="container-custom max-w-3xl text-center">
        <h1 className="text-9xl font-bold text-teamwork-blue mb-4">404</h1>
        <h2 className="heading-2 mb-6">Page Not Found</h2>
        <p className="text-xl text-gray-400 mb-12">
          Looks like this page doesn't exist. Let's get you back on track.
        </p>

        <div className="grid md:grid-cols-3 gap-6 mb-8">
          <Link href="/" className="card hover:border-teamwork-blue transition-all group">
            <FiHome className="w-12 h-12 text-teamwork-blue mx-auto mb-4 group-hover:scale-110 transition-transform" />
            <h3 className="font-semibold mb-2">Home</h3>
            <p className="text-sm text-gray-400">Return to homepage</p>
          </Link>

          <Link href="/services/" className="card hover:border-teamwork-blue transition-all group">
            <FiTool className="w-12 h-12 text-teamwork-blue mx-auto mb-4 group-hover:scale-110 transition-transform" />
            <h3 className="font-semibold mb-2">Services</h3>
            <p className="text-sm text-gray-400">View our services</p>
          </Link>

          <Link href="/contact/" className="card hover:border-teamwork-blue transition-all group">
            <FiPhone className="w-12 h-12 text-teamwork-blue mx-auto mb-4 group-hover:scale-110 transition-transform" />
            <h3 className="font-semibold mb-2">Contact</h3>
            <p className="text-sm text-gray-400">Get in touch</p>
          </Link>
        </div>

        <div className="flex flex-wrap gap-4 justify-center">
          <Link href="/book/" className="btn-primary">
            Book Same-Week Inspection
          </Link>
          <Link href="/estimate/" className="btn-secondary">
            Start Teamwork Estimate
          </Link>
          <a href="tel:9133963717" className="btn-secondary">
            Call 913-396-3717
          </a>
        </div>
      </div>
    </section>
  )
}
