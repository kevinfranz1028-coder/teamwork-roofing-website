'use client'

import Link from 'next/link'
import Image from 'next/image'
import { FiArrowRight } from 'react-icons/fi'
import { galleryProjects } from '@/content/gallery'

/**
 * Homepage Recent Work Strip
 *
 * Shows 3 most recent approved gallery projects
 * Only renders when at least 1 approved project exists
 * Hidden when gallery is empty (no homeowner approvals yet)
 */
export default function RecentWorkStrip() {
  // Only show if we have approved projects
  if (galleryProjects.length === 0) {
    return null
  }

  // Get up to 3 most recent approved projects with after images (sorted by date desc)
  // Filter out inspection-only projects (no after image)
  const recentProjects = [...galleryProjects]
    .filter(p => p.afterImage) // Only show projects with completed after photos
    .sort((a, b) => b.date.localeCompare(a.date))
    .slice(0, 3)

  return (
    <section className="section-padding bg-light-bg">
      <div className="container-custom">
        <div className="text-center mb-12">
          <h2 className="heading-2 mb-4">Recent Work</h2>
          <p className="text-lg text-text-secondary">
            Before & after transformations across Kansas City Metro
          </p>
        </div>

        <div className="grid md:grid-cols-3 gap-8 mb-12">
          {recentProjects.map(project => (
            <div key={project.id} className="card bg-white hover:border-teamwork-green transition-all duration-300 hover:shadow-lg">
              {/* After Image (primary) */}
              {project.afterImage && (
                <div className="relative aspect-[4/3] mb-4 rounded-lg overflow-hidden bg-gray-100">
                  <Image
                    src={project.afterImage}
                    alt={project.afterAlt || ''}
                    fill
                    className="object-cover"
                    loading="lazy"
                    sizes="(max-width: 768px) 100vw, 33vw"
                  />
                  <div className="absolute top-3 left-3 bg-teamwork-green text-white px-3 py-1 rounded-md text-sm font-semibold">
                    {project.afterCaption || 'After'}
                  </div>
                </div>
              )}

              {/* Project Details */}
              <p className="font-semibold mb-2 line-clamp-2">{project.description}</p>
              <p className="text-sm text-text-secondary">
                <span className="font-medium">{project.city}</span>
                {' • '}
                <span className="capitalize">{project.jobType.replace('-', ' ')}</span>
              </p>
            </div>
          ))}
        </div>

        {/* View All Gallery Link */}
        <div className="text-center">
          <Link
            href="/gallery/"
            className="inline-flex items-center gap-2 text-teamwork-green hover:text-teamwork-green-dark font-semibold group"
          >
            View Full Gallery
            <FiArrowRight className="w-5 h-5 group-hover:translate-x-1 transition-transform" />
          </Link>
        </div>
      </div>
    </section>
  )
}
