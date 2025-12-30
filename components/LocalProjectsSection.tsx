import Link from 'next/link'

interface Project {
  title: string
  scope: string
  city: string
}

interface LocalProjectsSectionProps {
  city: string
  projects?: Project[]
}

export default function LocalProjectsSection({ city, projects }: LocalProjectsSectionProps) {
  const defaultProjects: Project[] = [
    {
      title: 'Roof Replacement',
      scope: 'Architectural shingles + ridge vent + cleanup',
      city: city
    },
    {
      title: 'Storm Damage Repair',
      scope: 'Hail damage documentation + full roof replacement',
      city: city
    },
    {
      title: 'Gutter & Siding Upgrade',
      scope: 'Seamless gutters + guards + partial siding replacement',
      city: city
    }
  ]

  const displayProjects = projects || defaultProjects

  return (
    <section className="section-padding bg-dark-surface">
      <div className="container-custom">
        <h2 className="heading-2 mb-4 text-center">Projects Near You</h2>
        <p className="text-xl text-gray-400 text-center mb-12">
          Recent Teamwork projects completed in and around {city}, KS.
        </p>

        <div className="grid md:grid-cols-3 gap-6 mb-8">
          {displayProjects.slice(0, 3).map((project, index) => (
            <div key={index} className="card group">
              <div className="relative h-48 bg-dark-bg rounded-lg mb-4 overflow-hidden">
                <div className="absolute inset-0 flex items-center justify-center text-gray-600">
                  Project Photo
                </div>
              </div>
              <div className="mb-3">
                <span className="text-xs px-3 py-1 bg-teamwork-blue/10 text-teamwork-blue rounded-full">
                  {project.city}
                </span>
              </div>
              <h4 className="font-semibold mb-2">{project.title}</h4>
              <p className="text-sm text-gray-400 mb-4">{project.scope}</p>
              <Link href="/projects/" className="text-teamwork-blue hover:underline text-sm font-semibold">
                View Project →
              </Link>
            </div>
          ))}
        </div>

        <div className="text-center">
          <Link href="/projects/" className="btn-secondary">
            View All Projects
          </Link>
        </div>
      </div>
    </section>
  )
}
