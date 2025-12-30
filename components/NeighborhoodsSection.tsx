interface NeighborhoodsSectionProps {
  city: string
  neighborhoods: string[]
}

export default function NeighborhoodsSection({ city, neighborhoods }: NeighborhoodsSectionProps) {
  return (
    <section className="section-padding bg-dark-bg">
      <div className="container-custom">
        <div className="card max-w-4xl mx-auto">
          <h2 className="heading-3 mb-6 text-center">Neighborhoods We Serve in {city}</h2>
          <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
            {neighborhoods.map((neighborhood, index) => (
              <div key={index} className="flex items-center space-x-2">
                <span className="w-1.5 h-1.5 bg-teamwork-blue rounded-full flex-shrink-0"></span>
                <span className="text-gray-300 text-sm">{neighborhood}</span>
              </div>
            ))}
          </div>
        </div>
      </div>
    </section>
  )
}
