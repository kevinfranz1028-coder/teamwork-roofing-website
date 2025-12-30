import { FiStar, FiCheckCircle } from 'react-icons/fi'
import CTABand from '@/components/CTABand'

export const metadata = {
  title: 'Customer Reviews | Teamwork Roofing Kansas City',
  description: 'See what Kansas City Metro homeowners say about our roofing, gutter, siding, and window services.',
}

export default function ReviewsPage() {
  const reviews = [
    {
      name: 'Sarah M.',
      city: 'Overland Park',
      rating: 5,
      date: '2 weeks ago',
      text: 'True to their name — real teamwork. They kept us informed every step, left the property spotless, and the roof looks incredible. The photo documentation was so helpful for our records.'
    },
    {
      name: 'Mike T.',
      city: 'Lenexa',
      rating: 5,
      date: '1 month ago',
      text: 'After storm damage, they helped with documentation and made the insurance process so much easier. Highly recommend their full exterior inspection.'
    },
    {
      name: 'Jennifer K.',
      city: 'Olathe',
      rating: 5,
      date: '3 weeks ago',
      text: 'Same-week inspection promise delivered! Professional crew, clear communication, and beautiful results on our new gutters and siding.'
    },
    {
      name: 'David R.',
      city: 'Shawnee',
      rating: 5,
      date: '2 months ago',
      text: 'They replaced our roof and it was a flawless experience. Clean site guarantee is real — you would never know they were here except for the beautiful new roof.'
    },
    {
      name: 'Lisa P.',
      city: 'Leawood',
      rating: 5,
      date: '1 month ago',
      text: 'Financing options made our window replacement possible. No pressure sales, just clear options and professional installation.'
    },
    {
      name: 'Tom H.',
      city: 'Prairie Village',
      rating: 5,
      date: '3 months ago',
      text: 'Repaired our roof leak fast. Honest assessment, fair price, and they actually showed us photos of the problem and the fix. That is real partnership.'
    },
    {
      name: 'Amanda S.',
      city: 'Mission',
      rating: 5,
      date: '2 weeks ago',
      text: 'From estimate to final walkthrough, everything was professional. Our new siding transformed the house and the crew was respectful and efficient.'
    },
    {
      name: 'Kevin J.',
      city: 'Gardner',
      rating: 5,
      date: '1 month ago',
      text: 'Best roofing company we've worked with. Photo proof inspection gave us confidence, and the warranty backing shows they stand behind their work.'
    },
    {
      name: 'Michelle W.',
      city: 'Spring Hill',
      rating: 5,
      date: '3 weeks ago',
      text: 'They handled our storm damage claim with professionalism. Detailed documentation helped our insurance process go smoothly.'
    }
  ]

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
      <section className="section-padding bg-dark-bg">
        <div className="container-custom">
          <div className="text-center mb-12">
            <h1 className="heading-1 mb-6">Customer Reviews</h1>
            <p className="text-xl text-gray-400 mb-8">
              Real experiences from real partnerships across Kansas City Metro
            </p>
            <div className="flex items-center justify-center gap-2 mb-4">
              <div className="flex">
                {[...Array(5)].map((_, i) => (
                  <FiStar key={i} className="w-8 h-8 text-yellow-500 fill-current" />
                ))}
              </div>
              <span className="text-3xl font-bold">5.0</span>
            </div>
            <p className="text-gray-500">Based on {reviews.length}+ verified reviews</p>
          </div>

          {/* Top Mentions */}
          <div className="max-w-4xl mx-auto mb-16">
            <h2 className="heading-3 mb-6 text-center">What Customers Mention Most</h2>
            <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-4">
              {topMentions.map((mention, index) => (
                <div key={index} className="flex items-center space-x-2 card">
                  <FiCheckCircle className="w-5 h-5 text-teamwork-blue flex-shrink-0" />
                  <span className="text-gray-300">{mention}</span>
                </div>
              ))}
            </div>
          </div>

          {/* Reviews Grid */}
          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
            {reviews.map((review, index) => (
              <div key={index} className="card">
                <div className="flex mb-3">
                  {[...Array(review.rating)].map((_, i) => (
                    <FiStar key={i} className="w-5 h-5 text-yellow-500 fill-current" />
                  ))}
                </div>
                <p className="text-gray-300 mb-4">{review.text}</p>
                <div className="border-t border-dark-border pt-4">
                  <p className="font-semibold">{review.name}</p>
                  <p className="text-sm text-gray-400">{review.city}, KS</p>
                  <p className="text-xs text-gray-500 mt-1">{review.date}</p>
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      <CTABand title="Join Our Happy Customers" subtitle="Experience the Teamwork difference on your next project" />
    </>
  )
}
