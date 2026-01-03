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
    <section className="bg-gradient-to-r from-teamwork-green to-[#0094CC]">
      <div className="container-custom py-16">
        <div className="text-center mb-8">
          <h2 className="heading-2 mb-4 text-white">{title}</h2>
          <p className="text-xl text-white/90 max-w-2xl mx-auto">{subtitle}</p>
        </div>

        <div className="flex flex-col sm:flex-row gap-4 justify-center items-center">
          <Link href="/book/" className="px-6 py-3 bg-white text-teamwork-green font-semibold rounded-lg hover:bg-gray-100 transition-all shadow-lg">
            Book Same-Week Inspection
          </Link>
          <Link href="/estimate/" className="px-6 py-3 bg-transparent border-2 border-white text-white font-semibold rounded-lg hover:bg-white hover:text-teamwork-green transition-all">
            Start Teamwork Estimate
          </Link>
          <a href="tel:9133963717" className="px-6 py-3 bg-transparent border-2 border-white text-white font-semibold rounded-lg hover:bg-white hover:text-teamwork-green transition-all">
            Call 913-396-3717
          </a>
        </div>
      </div>
    </section>
  )
}
