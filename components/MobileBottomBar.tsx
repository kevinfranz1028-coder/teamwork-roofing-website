'use client'

import Link from 'next/link'
import { FiPhone, FiMessageSquare, FiClipboard, FiCalendar } from 'react-icons/fi'

export default function MobileBottomBar() {
  return (
    <div className="lg:hidden fixed bottom-0 left-0 right-0 bg-dark-surface border-t border-dark-border shadow-2xl z-40">
      <div className="grid grid-cols-4 gap-1">
        <a
          href="tel:9133963717"
          className="flex flex-col items-center justify-center py-3 text-gray-300 hover:text-teamwork-blue transition-colors"
        >
          <FiPhone className="w-5 h-5 mb-1" />
          <span className="text-xs">Call</span>
        </a>

        <a
          href="sms:9133963717"
          className="flex flex-col items-center justify-center py-3 text-gray-300 hover:text-teamwork-blue transition-colors"
        >
          <FiMessageSquare className="w-5 h-5 mb-1" />
          <span className="text-xs">Text</span>
        </a>

        <Link
          href="/estimate/"
          className="flex flex-col items-center justify-center py-3 text-gray-300 hover:text-teamwork-blue transition-colors"
        >
          <FiClipboard className="w-5 h-5 mb-1" />
          <span className="text-xs">Estimate</span>
        </Link>

        <Link
          href="/book/"
          className="flex flex-col items-center justify-center py-3 bg-teamwork-blue text-white"
        >
          <FiCalendar className="w-5 h-5 mb-1" />
          <span className="text-xs">Book</span>
        </Link>
      </div>
    </div>
  )
}
