'use client'

import Link from 'next/link'
import { FiPhone, FiCalendar } from 'react-icons/fi'

export default function MobileBottomBar() {
  return (
    <div className="lg:hidden fixed bottom-0 left-0 right-0 bg-white border-t-2 border-teamwork-green shadow-2xl z-40 safe-bottom">
      <div className="grid grid-cols-2 gap-2 p-2">
        <a
          href="tel:+19132779925"
          className="flex items-center justify-center gap-2 py-4 px-4 bg-white text-teamwork-green border-2 border-teamwork-green font-semibold rounded-lg hover:bg-teamwork-green hover:text-white transition-all active:scale-95 min-h-[44px]"
        >
          <FiPhone className="w-5 h-5" />
          <span>Call (913) 277-9925</span>
        </a>

        <Link
          href="/inspect/"
          className="flex items-center justify-center gap-2 py-4 px-4 bg-teamwork-green text-white font-semibold rounded-lg hover:bg-teamwork-green-dark transition-all active:scale-95 min-h-[44px]"
        >
          <FiCalendar className="w-5 h-5" />
          <span>Book Free Inspection</span>
        </Link>
      </div>
    </div>
  )
}
