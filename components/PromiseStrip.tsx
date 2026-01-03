import { FiShield, FiClock, FiCamera, FiDollarSign, FiCheckCircle } from 'react-icons/fi'

export default function PromiseStrip() {
  const promises = [
    {
      icon: FiShield,
      title: 'Teamwork Warranty',
      description: 'Backed by our commitment'
    },
    {
      icon: FiClock,
      title: 'Same-Week Inspection',
      description: 'Fast response guaranteed'
    },
    {
      icon: FiCheckCircle,
      title: 'Clean Site Guarantee',
      description: 'Your property protected'
    },
    {
      icon: FiCamera,
      title: 'Photo-Proof Inspection',
      description: 'Complete documentation'
    },
    {
      icon: FiDollarSign,
      title: 'Teamwork Financing',
      description: 'Flexible payment options'
    }
  ]

  return (
    <div className="bg-white border-y border-light-border">
      <div className="container-custom py-8">
        <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-5 gap-6">
          {promises.map((promise, index) => {
            const Icon = promise.icon
            return (
              <div key={index} className="flex flex-col items-center text-center">
                <div className="w-12 h-12 rounded-full bg-teamwork-green/10 flex items-center justify-center mb-3">
                  <Icon className="w-6 h-6 text-teamwork-green" />
                </div>
                <h4 className="font-semibold text-sm mb-1">{promise.title}</h4>
                <p className="text-xs text-text-secondary">{promise.description}</p>
              </div>
            )
          })}
        </div>
      </div>
    </div>
  )
}
