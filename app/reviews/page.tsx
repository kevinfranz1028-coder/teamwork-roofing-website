import { FiCheckCircle } from 'react-icons/fi'
import CTABand from '@/components/CTABand'
import TrustBlock from '@/components/TrustBlock'

export const metadata = {
  title: 'Customer Reviews | Teamwork Roofing Kansas City',
  description: 'See what Kansas City Metro homeowners say about our roofing, gutter, siding, and window services.',
}

export default function ReviewsPage() {
  const topMentions = [
    'Clean site practices',
    'Clear communication',
    'Photo documentation',
    'Professional crews',
    'Same-week response',
    'Honest recommendations'
  ]

  return (
    <>
      <section className="section-padding bg-light-bg">
        <div className="container-custom">
          <div className="text-center mb-12">
            <h1 className="heading-1 mb-6">Customer Reviews</h1>
            <p className="text-xl text-text-secondary mb-8">
              Real experiences from real partnerships across Kansas City Metro
            </p>
          </div>

          {/* Top Mentions */}
          <div className="max-w-4xl mx-auto mb-16">
            <h2 className="heading-3 mb-6 text-center">What Customers Mention Most</h2>
            <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-4">
              {topMentions.map((mention, index) => (
                <div key={index} className="group flex items-center space-x-2 card hover:border-teamwork-green transition-all duration-300 hover:shadow-lg hover:-translate-y-0.5">
                  <FiCheckCircle className="w-5 h-5 text-teamwork-green flex-shrink-0 group-hover:scale-110 transition-transform duration-300" />
                  <span className="text-text-secondary group-hover:text-teamwork-green transition-colors duration-300">{mention}</span>
                </div>
              ))}
            </div>
          </div>

          {/* Trust Block */}
          <div className="mb-12">
            <h2 className="heading-3 mb-8 text-center">Why Choose Teamwork Roofing</h2>
            <TrustBlock />
          </div>
        </div>
      </section>

      <CTABand title="Join Our Happy Customers" subtitle="Experience the Teamwork difference on your next project" />
    </>
  )
}
