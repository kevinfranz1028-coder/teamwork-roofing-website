'use client'

import { useEffect, useRef } from 'react'
import Image from 'next/image'
import { FiX, FiChevronLeft, FiChevronRight } from 'react-icons/fi'

interface LightboxProps {
  images: { src: string; alt: string }[]
  currentIndex: number
  onClose: () => void
  onNext: () => void
  onPrev: () => void
}

export default function Lightbox({ images, currentIndex, onClose, onNext, onPrev }: LightboxProps) {
  const closeButtonRef = useRef<HTMLButtonElement>(null)
  const prevButtonRef = useRef<HTMLButtonElement>(null)
  const nextButtonRef = useRef<HTMLButtonElement>(null)
  const overlayRef = useRef<HTMLDivElement>(null)
  const lastFocusedElement = useRef<HTMLElement | null>(null)

  // Focus trap and keyboard navigation
  useEffect(() => {
    // Store the element that opened the lightbox
    lastFocusedElement.current = document.activeElement as HTMLElement

    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape') {
        onClose()
      } else if (e.key === 'ArrowLeft') {
        onPrev()
      } else if (e.key === 'ArrowRight') {
        onNext()
      } else if (e.key === 'Tab') {
        // Focus trap: cycle through close/prev/next buttons
        const focusableElements = [
          closeButtonRef.current,
          prevButtonRef.current,
          nextButtonRef.current
        ].filter(Boolean) as HTMLButtonElement[]

        if (focusableElements.length === 0) return

        const currentIndex = focusableElements.indexOf(document.activeElement as HTMLButtonElement)
        e.preventDefault()

        if (e.shiftKey) {
          // Shift+Tab: go backwards
          const prevIndex = currentIndex <= 0 ? focusableElements.length - 1 : currentIndex - 1
          focusableElements[prevIndex]?.focus()
        } else {
          // Tab: go forwards
          const nextIndex = currentIndex >= focusableElements.length - 1 ? 0 : currentIndex + 1
          focusableElements[nextIndex]?.focus()
        }
      }
    }

    // Focus the close button on mount
    closeButtonRef.current?.focus()

    document.addEventListener('keydown', handleKeyDown)
    document.body.style.overflow = 'hidden'

    return () => {
      document.removeEventListener('keydown', handleKeyDown)
      document.body.style.overflow = ''

      // Return focus to the opening element
      if (lastFocusedElement.current) {
        lastFocusedElement.current.focus()
      }
    }
  }, [onClose, onNext, onPrev])

  const current = images[currentIndex]

  return (
    <div
      ref={overlayRef}
      role="dialog"
      aria-modal="true"
      aria-label="Image lightbox"
      className="fixed inset-0 z-50 bg-black/90 flex items-center justify-center p-4"
      onClick={(e) => {
        if (e.target === overlayRef.current) {
          onClose()
        }
      }}
    >
      {/* Close button */}
      <button
        ref={closeButtonRef}
        onClick={onClose}
        className="absolute top-4 right-4 p-2 bg-white/10 hover:bg-white/20 rounded-full transition-colors focus:outline-none focus:ring-2 focus:ring-white"
        aria-label="Close lightbox"
      >
        <FiX className="w-6 h-6 text-white" />
      </button>

      {/* Navigation */}
      {images.length > 1 && (
        <>
          <button
            ref={prevButtonRef}
            onClick={onPrev}
            className="absolute left-4 p-2 bg-white/10 hover:bg-white/20 rounded-full transition-colors focus:outline-none focus:ring-2 focus:ring-white"
            aria-label="Previous image"
          >
            <FiChevronLeft className="w-6 h-6 text-white" />
          </button>
          <button
            ref={nextButtonRef}
            onClick={onNext}
            className="absolute right-4 md:right-20 p-2 bg-white/10 hover:bg-white/20 rounded-full transition-colors focus:outline-none focus:ring-2 focus:ring-white"
            aria-label="Next image"
          >
            <FiChevronRight className="w-6 h-6 text-white" />
          </button>
        </>
      )}

      {/* Image */}
      <div className="relative max-w-6xl w-full h-full flex flex-col items-center justify-center">
        <div className="relative w-full max-h-[80vh] aspect-[4/3]">
          <Image
            src={current.src}
            alt={current.alt}
            fill
            className="object-contain"
            sizes="100vw"
            priority
          />
        </div>

        {/* Counter */}
        <div className="mt-4 text-white text-sm">
          {currentIndex + 1} / {images.length}
        </div>
      </div>
    </div>
  )
}
