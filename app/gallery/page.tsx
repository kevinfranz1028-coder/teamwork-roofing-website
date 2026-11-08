'use client'

import { useState } from 'react'
import Image from 'next/image'
import Link from 'next/link'
import { FiFilter, FiPhone } from 'react-icons/fi'
import { galleryProjects, type GalleryProject } from '@/content/gallery'
import CTABand from '@/components/CTABand'
import Lightbox from '@/components/Lightbox'

export default function GalleryPage() {
  const [cityFilter, setCityFilter] = useState<string>('All')
  const [jobTypeFilter, setJobTypeFilter] = useState<string>('All')
  const [lightboxImages, setLightboxImages] = useState<{ src: string; alt: string }[]>([])
  const [lightboxIndex, setLightboxIndex] = useState(0)

  const cities = ['All', 'Overland Park', 'Leawood', 'Lenexa', 'Kansas City', 'Olathe', 'Other']
  const jobTypes = [
    { value: 'All', label: 'All Projects' },
    { value: 'full-replacement', label: 'Full Replacement' },
    { value: 'storm-hail', label: 'Storm/Hail Damage' },
    { value: 'inspection', label: 'Inspection' },
    { value: 'repair', label: 'Repair' },
    { value: 'gutter', label: 'Gutter Work' },
    { value: 'siding', label: 'Siding' }
  ]

  const filteredProjects = galleryProjects.filter(project => {
    const cityMatch = cityFilter === 'All' || project.city === cityFilter
    const jobTypeMatch = jobTypeFilter === 'All' || project.jobType === jobTypeFilter
    return cityMatch && jobTypeMatch
  })

  return (
    <>
      <section className="section-padding bg-light-bg">
        <div className="container-custom">
          <div className="text-center mb-12">
            <h1 className="heading-1 mb-6">Project Gallery</h1>
            <p className="text-xl text-text-secondary">
              Before & after transformations across Kansas City Metro
            </p>
          </div>

          {/* Filters */}
          {galleryProjects.length > 0 && (
            <div className="max-w-4xl mx-auto mb-12">
              <div className="card bg-white">
                <div className="flex items-center gap-2 mb-4">
                  <FiFilter className="w-5 h-5 text-teamwork-green" />
                  <h2 className="font-semibold">Filter Projects</h2>
                </div>

                <div className="grid md:grid-cols-2 gap-4">
                  {/* City Filter */}
                  <div>
                    <label htmlFor="city-filter" className="block text-sm font-medium mb-2">
                      City
                    </label>
                    <select
                      id="city-filter"
                      value={cityFilter}
                      onChange={(e) => setCityFilter(e.target.value)}
                      className="w-full px-4 py-2 border border-light-border rounded-lg focus:ring-2 focus:ring-teamwork-green focus:border-transparent"
                    >
                      {cities.map(city => (
                        <option key={city} value={city}>{city}</option>
                      ))}
                    </select>
                  </div>

                  {/* Job Type Filter */}
                  <div>
                    <label htmlFor="job-type-filter" className="block text-sm font-medium mb-2">
                      Project Type
                    </label>
                    <select
                      id="job-type-filter"
                      value={jobTypeFilter}
                      onChange={(e) => setJobTypeFilter(e.target.value)}
                      className="w-full px-4 py-2 border border-light-border rounded-lg focus:ring-2 focus:ring-teamwork-green focus:border-transparent"
                    >
                      {jobTypes.map(type => (
                        <option key={type.value} value={type.value}>{type.label}</option>
                      ))}
                    </select>
                  </div>
                </div>

                {filteredProjects.length === 0 && galleryProjects.length > 0 && (
                  <p className="text-center text-text-secondary mt-6">
                    No projects match your filters. Try adjusting your selection.
                  </p>
                )}
              </div>
            </div>
          )}

          {/* Gallery Grid - Empty State */}
          {galleryProjects.length === 0 ? (
            <div className="max-w-2xl mx-auto text-center py-16">
              <div className="card bg-white">
                <div className="w-20 h-20 mx-auto mb-6 rounded-full bg-teamwork-green/10 flex items-center justify-center">
                  <FiPhone className="w-10 h-10 text-teamwork-green" />
                </div>
                <h2 className="heading-3 mb-4">Project Photos Coming Soon</h2>
                <p className="text-text-secondary mb-8">
                  We're currently gathering before-and-after photos of our Kansas City Metro projects.
                  Check back soon to see the Teamwork difference!
                </p>
                <div className="flex flex-col sm:flex-row gap-4 justify-center">
                  <a
                    href="tel:9132779925"
                    className="btn-primary inline-flex items-center justify-center"
                  >
                    <FiPhone className="mr-2 w-5 h-5" />
                    Call (913) 277-9925
                  </a>
                  <Link href="/inspect/" className="btn-secondary">
                    Book Free Inspection
                  </Link>
                </div>
              </div>
            </div>
          ) : (
            /* Gallery Grid - With Projects */
            <div className="space-y-8">
              {filteredProjects.map(project => {
                // Special handling for inspection projects (afterPending)
                const isInspection = project.afterPending === true

                // For olathe-002: show beforeImage (main photo) + specific supporting photos
                const olatheFeatures = isInspection && project.id === 'olathe-002'
                  ? [
                      project.beforeImage, // Main photo (before-1) shown first
                      project.additionalImages?.find(img => /-before-2\.jpg$/.test(img)),
                      project.additionalImages?.find(img => /-before-3\.jpg$/.test(img)),
                      project.additionalImages?.find(img => /-detail-3\.jpg$/.test(img)),
                      project.additionalImages?.find(img => /-detail-5\.jpg$/.test(img))
                    ].filter(Boolean) as string[]
                  : []

                const featuredImages = olatheFeatures

                const lightboxOnlyImages = isInspection && project.id === 'olathe-002' && project.additionalImages
                  ? project.additionalImages.filter(img => !featuredImages.includes(img))
                  : []

                // Cap kansas-city-ks-002 at 600px max-width
                const maxWidthClass = project.id === 'kansas-city-ks-002' ? 'max-w-[600px] mx-auto' : ''

                return (
                  <div key={project.id} className={`card bg-white hover:border-teamwork-green transition-all duration-300 hover:shadow-lg ${maxWidthClass}`}>
                    {/* Inspection Layout */}
                    {isInspection ? (
                      <div>
                        <h2 className="text-2xl font-bold mb-4">{project.description}</h2>

                        {/* Featured inspection images grid */}
                        {featuredImages.length > 0 && (
                          <div className="grid grid-cols-2 md:grid-cols-3 gap-4 mb-4">
                            {featuredImages.map((img, idx) => {
                              // Generate specific alt text for olathe-002 inspection photos
                              const altTexts = [
                                `Hail damage inspection overview, ${project.city}`,
                                `Roof damage close-up view, ${project.city} inspection`,
                                `Shingle impact detail, ${project.city} inspection`,
                                `Granule loss from hail, ${project.city} inspection`,
                                `Asphalt shingle damage assessment, ${project.city} inspection`
                              ]
                              return (
                                <div key={idx} className="relative aspect-[4/3] rounded-lg overflow-hidden bg-gray-100">
                                  <Image
                                    src={img}
                                    alt={altTexts[idx] || `Inspection detail ${idx + 1}, ${project.city}`}
                                    fill
                                    className="object-cover"
                                    loading="lazy"
                                    sizes="(max-width: 768px) 50vw, 33vw"
                                  />
                                </div>
                              )
                            })}
                          </div>
                        )}

                        {/* Lightbox trigger for remaining images */}
                        {lightboxOnlyImages.length > 0 && (
                          <button
                            onClick={() => {
                              setLightboxImages(lightboxOnlyImages.map((src, idx) => ({
                                src,
                                alt: `Additional inspection photo ${idx + 1} - ${project.city}`
                              })))
                              setLightboxIndex(0)
                            }}
                            className="btn-secondary w-full mb-4"
                          >
                            View {lightboxOnlyImages.length} More Photos
                          </button>
                        )}

                        {/* Project details */}
                        <div className="pt-4 border-t border-light-border">
                          <p className="text-sm text-text-secondary">
                            <span className="font-medium">{project.city}</span>
                            {' • '}
                            <span className="capitalize">{project.jobType.replace('-', ' ')}</span>
                          </p>
                        </div>
                      </div>
                    ) : (
                      /* Standard Before/After Layout */
                      <>
                        <div className={`grid gap-6 ${project.afterImage ? 'md:grid-cols-2' : 'md:grid-cols-1'} ${project.id === 'kansas-city-ks-002' ? 'max-w-[600px] mx-auto' : ''}`}>
                          {/* Before Image */}
                          <div>
                            <div className={`relative aspect-[4/3] mb-3 rounded-lg overflow-hidden bg-gray-100 ${project.id === 'kansas-city-ks-002' ? 'max-w-full' : ''}`}>
                              <Image
                                src={project.beforeImage}
                                alt={project.beforeAlt}
                                fill
                                className={`${project.id === 'kansas-city-ks-002' ? 'object-contain' : 'object-cover'}`}
                                loading="lazy"
                                sizes="(max-width: 768px) 100vw, 50vw"
                                style={project.id === 'kansas-city-ks-002' ? { maxWidth: '600px' } : undefined}
                              />
                              <div className="absolute top-3 left-3 bg-red-600 text-white px-3 py-1 rounded-md text-sm font-semibold z-10">
                                {project.beforeCaption || 'Before'}
                              </div>
                            </div>
                          </div>

                          {/* After Image (only if exists) */}
                          {project.afterImage && (
                            <div>
                              <div className={`relative aspect-[4/3] mb-3 rounded-lg overflow-hidden bg-gray-100 ${project.id === 'kansas-city-ks-002' ? 'max-w-full' : ''}`}>
                                <Image
                                  src={project.afterImage}
                                  alt={project.afterAlt || ''}
                                  fill
                                  className={`${project.id === 'kansas-city-ks-002' ? 'object-contain' : 'object-cover'}`}
                                  loading="lazy"
                                  sizes="(max-width: 768px) 100vw, 50vw"
                                  style={project.id === 'kansas-city-ks-002' ? { maxWidth: '600px' } : undefined}
                                />
                                <div className="absolute top-3 left-3 bg-teamwork-green text-white px-3 py-1 rounded-md text-sm font-semibold z-10">
                                  {project.afterCaption || 'After'}
                                </div>
                              </div>
                            </div>
                          )}
                        </div>

                        {/* Additional images for standard projects */}
                        {project.additionalImages && project.additionalImages.length > 0 && (
                          <div className="mt-4">
                            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                              {project.additionalImages.slice(0, 4).map((img, idx) => (
                                <div key={idx} className="relative aspect-[4/3] rounded-lg overflow-hidden bg-gray-100">
                                  <Image
                                    src={img}
                                    alt={`Additional detail ${idx + 1} - ${project.city}`}
                                    fill
                                    className="object-cover"
                                    loading="lazy"
                                    sizes="(max-width: 768px) 50vw, 25vw"
                                  />
                                </div>
                              ))}
                            </div>
                            {project.additionalImages.length > 4 && (
                              <button
                                onClick={() => {
                                  setLightboxImages(project.additionalImages!.map((src, idx) => ({
                                    src,
                                    alt: `Additional photo ${idx + 1} - ${project.city}`
                                  })))
                                  setLightboxIndex(0)
                                }}
                                className="btn-secondary w-full mt-4"
                              >
                                View All {project.additionalImages.length} Photos
                              </button>
                            )}
                          </div>
                        )}

                        {/* Project Details */}
                        <div className="mt-4 pt-4 border-t border-light-border">
                          <p className="font-semibold text-lg mb-2">{project.description}</p>
                          <p className="text-sm text-text-secondary">
                            <span className="font-medium">{project.city}</span>
                            {' • '}
                            <span className="capitalize">{project.jobType.replace('-', ' ')}</span>
                          </p>
                        </div>
                      </>
                    )}
                  </div>
                )
              })}
            </div>
          )}
        </div>
      </section>

      {/* Lightbox */}
      {lightboxImages.length > 0 && (
        <Lightbox
          images={lightboxImages}
          currentIndex={lightboxIndex}
          onClose={() => setLightboxImages([])}
          onNext={() => setLightboxIndex((lightboxIndex + 1) % lightboxImages.length)}
          onPrev={() => setLightboxIndex((lightboxIndex - 1 + lightboxImages.length) % lightboxImages.length)}
        />
      )}

      <CTABand title="Ready for Your Own Transformation?" subtitle="Same-week inspections available. Book online or call now." />
    </>
  )
}
