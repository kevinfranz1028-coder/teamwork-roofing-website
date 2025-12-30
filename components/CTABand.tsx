import Link from 'next/link'

interface CTABandProps {
  title?: string
  subtitle?: string
}

export default function CTABand({
  title = "Ready to Get Started?",
  subtitle = "Book your same-week inspection or get a quick estimate today"
}: CTABandProps) {
  return (
    <section className="bg-gradient-to-r from-teamwork-blue to-blue-700">
      <div className="container-custom py-16">
        <div className="text-center mb-8">
          <h2 className="heading-2 mb-4">{title}</h2>
          <p className="text-xl text-blue-100 max-w-2xl mx-auto">{subtitle}</p>
        </div>

        <div className="flex flex-col sm:flex-row gap-4 justify-center items-center">
          <Link href="/book/" className="btn-primary bg-white text-teamwork-blue hover:bg-gray-100">
            Book Same-Week Inspection
          </Link>
          <Link href="/estimate/" className="btn-secondary border-white text-white hover:bg-white hover:text-teamwork-blue">
            Start Teamwork Estimate
          </Link>
          <a href="tel:9133963717" className="btn-secondary border-white text-white hover:bg-white hover:text-teamwork-blue">
            Call 913-396-3717
          </a>
        </div>
      </div>
    </section>
  )
}
