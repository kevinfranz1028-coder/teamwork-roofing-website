import Link from 'next/link'
import { FiPhone } from 'react-icons/fi'
import ResponsiveImage from './ResponsiveImage'

export default function HomeHero() {
  return (
    <section className="relative bg-gradient-to-br from-teamwork-green to-green-700">
      <div className="container-custom section-padding">
        <div className="grid lg:grid-cols-2 gap-8 items-center">
          {/* Text Content */}
          <div className="text-white">
            <h1 className="heading-1 mb-6">
              Professional Roofing Services in Kansas City Metro
            </h1>
            <p className="text-xl mb-8 text-green-50">
              Bonded contractor. Lifetime workmanship warranty. Same-week inspections.
            </p>
            <div className="flex flex-col sm:flex-row gap-4">
              <a
                href="tel:+19132779925"
                className="btn-primary bg-white text-teamwork-green hover:bg-gray-100 inline-flex items-center justify-center gap-2"
              >
                <FiPhone className="w-5 h-5" />
                Call (913) 277-9925
              </a>
              <Link href="/inspect/" className="btn-secondary border-white text-white hover:bg-white hover:text-teamwork-green">
                Book Free Inspection
              </Link>
            </div>
          </div>

          {/* Before/After Images */}
          <div className="grid grid-cols-2 gap-4">
            {/* During Roof Replacement */}
            <div>
              <div className="relative aspect-[3/4] rounded-lg overflow-hidden bg-gray-100">
                <ResponsiveImage
                  src="/gallery/kansas-city-ks-001/kansas-city-ks-001-before-1.jpg"
                  alt="Asphalt shingle roof during replacement work in Kansas City, KS"
                  priority
                />
                <div className="absolute bottom-3 left-3 bg-black/70 text-white px-3 py-1 rounded-md text-sm font-semibold z-10">
                  During roof replacement
                </div>
              </div>
            </div>

            {/* Completed Roof */}
            <div>
              <div className="relative aspect-[3/4] rounded-lg overflow-hidden bg-gray-100">
                <ResponsiveImage
                  src="/gallery/kansas-city-ks-001/kansas-city-ks-001-after-1.jpg"
                  alt="Completed asphalt shingle roof in Kansas City, KS"
                  priority
                />
                <div className="absolute bottom-3 left-3 bg-teamwork-green text-white px-3 py-1 rounded-md text-sm font-semibold z-10">
                  Completed roof
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>
  )
}
