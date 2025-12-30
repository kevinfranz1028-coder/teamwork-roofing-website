'use client'

import { useState } from 'react'
import CTABand from '@/components/CTABand'

export default function ProjectsPage() {
  const [filter, setFilter] = useState('all')

  const projects = [
    { id: 1, city: 'Overland Park', service: 'Roof Replacement', category: 'roofing', image: '/projects/placeholder.jpg' },
    { id: 2, city: 'Lenexa', service: 'Storm Repair', category: 'storm', image: '/projects/placeholder.jpg' },
    { id: 3, city: 'Olathe', service: 'Gutters & Siding', category: 'gutters', image: '/projects/placeholder.jpg' },
    { id: 4, city: 'Kansas City', service: 'Roof Repair', category: 'roofing', image: '/projects/placeholder.jpg' },
    { id: 5, city: 'Shawnee', service: 'Full Exterior', category: 'storm', image: '/projects/placeholder.jpg' },
    { id: 6, city: 'Leawood', service: 'Roof Replacement', category: 'roofing', image: '/projects/placeholder.jpg' },
    { id: 7, city: 'Prairie Village', service: 'Siding Installation', category: 'siding', image: '/projects/placeholder.jpg' },
    { id: 8, city: 'Mission', service: 'Window Replacement', category: 'windows', image: '/projects/placeholder.jpg' },
    { id: 9, city: 'Merriam', service: 'Seamless Gutters', category: 'gutters', image: '/projects/placeholder.jpg' },
    { id: 10, city: 'Gardner', service: 'Roof & Gutters', category: 'roofing', image: '/projects/placeholder.jpg' },
    { id: 11, city: 'Spring Hill', service: 'Storm Assessment', category: 'storm', image: '/projects/placeholder.jpg' },
    { id: 12, city: 'De Soto', service: 'Complete Siding', category: 'siding', image: '/projects/placeholder.jpg' }
  ]

  const filteredProjects = filter === 'all' ? projects : projects.filter(p => p.category === filter)

  return (
    <>
      <section className="section-padding bg-dark-bg">
        <div className="container-custom">
          <div className="text-center mb-12">
            <h1 className="heading-1 mb-6">Our Projects</h1>
            <p className="text-xl text-gray-400 mb-8">
              Real work, real results across Kansas City Metro
            </p>

            {/* Filters */}
            <div className="flex flex-wrap justify-center gap-3">
              <button
                onClick={() => setFilter('all')}
                className={`px-6 py-2 rounded-lg font-semibold transition-all ${
                  filter === 'all'
                    ? 'bg-teamwork-blue text-white'
                    : 'bg-dark-surface text-gray-400 hover:text-white border border-dark-border'
                }`}
              >
                All Projects
              </button>
              <button
                onClick={() => setFilter('roofing')}
                className={`px-6 py-2 rounded-lg font-semibold transition-all ${
                  filter === 'roofing'
                    ? 'bg-teamwork-blue text-white'
                    : 'bg-dark-surface text-gray-400 hover:text-white border border-dark-border'
                }`}
              >
                Roofing
              </button>
              <button
                onClick={() => setFilter('storm')}
                className={`px-6 py-2 rounded-lg font-semibold transition-all ${
                  filter === 'storm'
                    ? 'bg-teamwork-blue text-white'
                    : 'bg-dark-surface text-gray-400 hover:text-white border border-dark-border'
                }`}
              >
                Storm
              </button>
              <button
                onClick={() => setFilter('gutters')}
                className={`px-6 py-2 rounded-lg font-semibold transition-all ${
                  filter === 'gutters'
                    ? 'bg-teamwork-blue text-white'
                    : 'bg-dark-surface text-gray-400 hover:text-white border border-dark-border'
                }`}
              >
                Gutters
              </button>
              <button
                onClick={() => setFilter('siding')}
                className={`px-6 py-2 rounded-lg font-semibold transition-all ${
                  filter === 'siding'
                    ? 'bg-teamwork-blue text-white'
                    : 'bg-dark-surface text-gray-400 hover:text-white border border-dark-border'
                }`}
              >
                Siding
              </button>
              <button
                onClick={() => setFilter('windows')}
                className={`px-6 py-2 rounded-lg font-semibold transition-all ${
                  filter === 'windows'
                    ? 'bg-teamwork-blue text-white'
                    : 'bg-dark-surface text-gray-400 hover:text-white border border-dark-border'
                }`}
              >
                Windows
              </button>
            </div>
          </div>

          {/* Project Grid */}
          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
            {filteredProjects.map((project) => (
              <div key={project.id} className="card group cursor-pointer hover:border-teamwork-blue transition-all">
                <div className="relative h-48 bg-dark-bg rounded-lg mb-4 overflow-hidden">
                  <div className="absolute inset-0 flex items-center justify-center text-gray-600">
                    Project Photo
                  </div>
                </div>
                <div className="flex justify-between items-start">
                  <div>
                    <h4 className="font-semibold mb-1">{project.service}</h4>
                    <p className="text-sm text-gray-400">{project.city}, KS</p>
                  </div>
                  <span className="text-xs px-3 py-1 bg-teamwork-blue/10 text-teamwork-blue rounded-full">
                    {project.city}
                  </span>
                </div>
              </div>
            ))}
          </div>

          {filteredProjects.length === 0 && (
            <div className="text-center py-12">
              <p className="text-gray-500">No projects found for this filter.</p>
            </div>
          )}
        </div>
      </section>

      <CTABand title="Ready to Start Your Project?" />
    </>
  )
}
