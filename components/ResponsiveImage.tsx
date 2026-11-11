interface ResponsiveImageProps {
  src: string
  alt: string
  className?: string
  priority?: boolean
}

/**
 * Responsive gallery image component
 * Serves WebP with JPG fallback, only widths that exist
 * Never serves full-size originals when sized copies exist
 */
export default function ResponsiveImage({ src, alt, className = '', priority = false }: ResponsiveImageProps) {
  // Extract base path and filename
  const basePath = src.replace(/\.(jpg|jpeg|webp)$/i, '')

  // Determine which sizes exist based on actual source dimensions
  // kansas-city-ks-002: all sources < 900px (only 640w exists)
  // kansas-city-ks-001 after-1/after-2: 1200px sources (only 640w exists)
  // Most others: >= 1500px sources (640w + 1280w exist)

  const filename = src.split('/').pop() || ''

  // Files that only have 640w (source < 1280px)
  const only640w =
    src.includes('kansas-city-ks-002') || // All sources 800-900px
    (filename.match(/-after-[12]\.jpg$/) && src.includes('kansas-city-ks-001')) // 1200px sources

  const has1280 = !only640w

  return (
    <picture>
      {/* WebP sources */}
      <source
        type="image/webp"
        srcSet={has1280
          ? `${basePath}-640w.webp 640w, ${basePath}-1280w.webp 1280w`
          : `${basePath}-640w.webp 640w`
        }
        sizes="(max-width: 768px) 100vw, 50vw"
      />
      {/* JPG fallback */}
      <source
        type="image/jpeg"
        srcSet={has1280
          ? `${basePath}-640w.jpg 640w, ${basePath}-1280w.jpg 1280w`
          : `${basePath}-640w.jpg 640w`
        }
        sizes="(max-width: 768px) 100vw, 50vw"
      />
      {/* Ultimate fallback */}
      <img
        src={src}
        alt={alt}
        className={`w-full h-full object-cover ${className}`}
        style={{ position: 'absolute', inset: 0 }}
        loading={priority ? 'eager' : 'lazy'}
      />
    </picture>
  )
}
