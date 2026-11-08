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

  // Determine which sizes exist based on source image dimensions
  // 640w exists for all, 1280w exists for images >= 1280px wide
  const has1280 = !src.includes('kansas-city-ks-002') && !src.includes('after-1') && !src.includes('after-2')

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
