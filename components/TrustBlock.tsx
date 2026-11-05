import { FiShield, FiCheckCircle, FiMapPin } from 'react-icons/fi'
import ReviewLinkPlaceholder from './ReviewLinkPlaceholder'

export default function TrustBlock() {
  return (
    <div className="max-w-4xl mx-auto">
      <div className="grid md:grid-cols-3 gap-6 mb-8">
        <div className="card text-center hover:border-teamwork-green transition-all duration-300 hover:shadow-lg hover:-translate-y-0.5">
          <div className="w-12 h-12 mx-auto mb-4 rounded-full bg-teamwork-green/10 flex items-center justify-center">
            <FiShield className="w-6 h-6 text-teamwork-green" />
          </div>
          <h3 className="font-semibold mb-2">Lifetime Workmanship Warranty</h3>
          <p className="text-sm text-text-secondary">
            Our work is backed by a lifetime workmanship warranty
          </p>
        </div>

        <div className="card text-center hover:border-teamwork-green transition-all duration-300 hover:shadow-lg hover:-translate-y-0.5">
          <div className="w-12 h-12 mx-auto mb-4 rounded-full bg-teamwork-green/10 flex items-center justify-center">
            <FiCheckCircle className="w-6 h-6 text-teamwork-green" />
          </div>
          <h3 className="font-semibold mb-2">Bonded</h3>
          <p className="text-sm text-text-secondary">
            Fully bonded for your protection and peace of mind
          </p>
        </div>

        <div className="card text-center hover:border-teamwork-green transition-all duration-300 hover:shadow-lg hover:-translate-y-0.5">
          <div className="w-12 h-12 mx-auto mb-4 rounded-full bg-teamwork-green/10 flex items-center justify-center">
            <FiMapPin className="w-6 h-6 text-teamwork-green" />
          </div>
          <h3 className="font-semibold mb-2">Local Overland Park Office</h3>
          <p className="text-sm text-text-secondary">
            8595 College Blvd, Suite 150-J, Overland Park, KS 66210
          </p>
        </div>
      </div>

      <ReviewLinkPlaceholder />
    </div>
  )
}
