'use client'

import { useState } from 'react'
import Image from 'next/image'
import Link from 'next/link'
import { FiFilter, FiPhone } from 'react-icons/fi'
import { galleryProjects, type GalleryProject } from '@/content/gallery'
import CTABand from '@/components/CTABand'

export default function GalleryPage() {
  const [cityFilter, setCityFilter] = useState<string>('All')
  const [jobTypeFilter, setJobTypeFilter] = useState<string>('All')

  const cities = ['All', 'Overland Park', 'Leawood', 'Lenexa', 'Kansas City', 'Olathe', 'Other']
  const jobTypes = [
    { value: 'All', label: 'All Projects' },
    { value: 'full-replacement', label: 'Full Replacement' },
    { value: 'storm-hail', label: 'Storm/Hail Damage' },
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
              {filteredProjects.map(project => (
                <div key={project.id} className="card bg-white hover:border-teamwork-green transition-all duration-300 hover:shadow-lg">
                  <div className="grid md:grid-cols-2 gap-6">
                    {/* Before Image */}
                    <div>
                      <div className="relative aspect-[4/3] mb-3 rounded-lg overflow-hidden bg-gray-100">
                        <Image
                          src={project.beforeImage}
                          alt={project.beforeAlt}
                          fill
                          className="object-cover"
                          loading="lazy"
                          sizes="(max-width: 768px) 100vw, 50vw"
                        />
                        <div className="absolute top-3 left-3 bg-red-600 text-white px-3 py-1 rounded-md text-sm font-semibold">
                          Before
                        </div>
                      </div>
                    </div>

                    {/* After Image */}
                    <div>
                      <div className="relative aspect-[4/3] mb-3 rounded-lg overflow-hidden bg-gray-100">
                        <Image
                          src={project.afterImage}
                          alt={project.afterAlt}
                          fill
                          className="object-cover"
                          loading="lazy"
                          sizes="(max-width: 768px) 100vw, 50vw"
                        />
                        <div className="absolute top-3 left-3 bg-teamwork-green text-white px-3 py-1 rounded-md text-sm font-semibold">
                          After
                        </div>
                      </div>
                    </div>
                  </div>

                  {/* Project Details */}
                  <div className="mt-4 pt-4 border-t border-light-border">
                    <p className="font-semibold text-lg mb-2">{project.description}</p>
                    <p className="text-sm text-text-secondary">
                      <span className="font-medium">{project.city}</span>
                      {' • '}
                      <span className="capitalize">{project.jobType.replace('-', ' ')}</span>
                    </p>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </section>

      <CTABand title="Ready for Your Own Transformation?" subtitle="Same-week inspections available. Book online or call now." />
    </>
  )
}
