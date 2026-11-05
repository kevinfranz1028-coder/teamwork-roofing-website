import { FiStar } from 'react-icons/fi'

// Config: Set GOOGLE_REVIEW_URL when Google Business Profile is created
const GOOGLE_REVIEW_URL = '' // Empty = component renders nothing

export default function ReviewLinkPlaceholder() {
  if (!GOOGLE_REVIEW_URL) {
    return null
  }

  return (
    <div className="text-center">
      <a
        href={GOOGLE_REVIEW_URL}
        target="_blank"
        rel="noopener noreferrer"
        className="inline-flex items-center gap-2 px-6 py-3 bg-white border-2 border-teamwork-green text-teamwork-green font-semibold rounded-lg hover:bg-teamwork-green hover:text-white transition-all"
      >
        <FiStar className="w-5 h-5" />
        Read Our Google Reviews
      </a>
    </div>
  )
}
