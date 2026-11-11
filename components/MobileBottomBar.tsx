'use client'

import Link from 'next/link'
import { FiPhone, FiCalendar } from 'react-icons/fi'

export default function MobileBottomBar() {
  return (
    <div className="lg:hidden fixed bottom-0 left-0 right-0 bg-white border-t-2 border-teamwork-green shadow-2xl z-40">
      <div className="grid grid-cols-2 gap-2 p-2">
        <a
          href="tel:+19132779925"
          className="flex items-center justify-center gap-1.5 py-3 px-2 sm:px-4 bg-white text-teamwork-green border-2 border-teamwork-green font-semibold rounded-lg hover:bg-teamwork-green hover:text-white transition-all active:scale-95 min-h-[44px] text-sm sm:text-base"
          aria-label="Call (913) 277-9925"
        >
          <FiPhone className="w-5 h-5 flex-shrink-0" />
          <span className="hidden sm:inline">Call (913) 277-9925</span>
          <span className="sm:hidden">Call</span>
        </a>

        <Link
          href="/inspect/"
          className="flex items-center justify-center gap-1.5 py-3 px-2 sm:px-4 bg-teamwork-green text-white font-semibold rounded-lg hover:bg-teamwork-green-dark transition-all active:scale-95 min-h-[44px] text-sm sm:text-base"
          aria-label="Book Free Inspection"
        >
          <FiCalendar className="w-5 h-5 flex-shrink-0" />
          <span className="hidden sm:inline">Book Inspection</span>
          <span className="sm:hidden">Book</span>
        </Link>
      </div>
    </div>
  )
}
