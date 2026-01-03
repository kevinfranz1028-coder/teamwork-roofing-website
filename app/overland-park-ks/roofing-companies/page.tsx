import Link from 'next/link'
import { FiCheckCircle, FiX, FiAlertTriangle } from 'react-icons/fi'
import CTABand from '@/components/CTABand'
import LocalProjectsSection from '@/components/LocalProjectsSection'

export const metadata = {
  title: 'Best Roofing Companies in Overland Park, KS | Hiring Checklist | Teamwork',
  description: 'How to choose a roofing company in Overland Park. Checklist, questions to ask, red flags to avoid. Make an informed decision.',
}

export default function RoofingCompaniesPage() {
  const checklist = [
    'Licensed and insured in Kansas',
    'Local references and reviews',
    'Written estimates with clear scope',
    'Photo documentation included',
    'Clean site practices and property protection',
    'Clear warranty on workmanship',
    'Material warranty details explained',
    'Timeline and schedule provided',
    'Financing options if needed',
    'No-pressure sales approach',
    'Emergency/urgent service availability',
    'Transparent communication'
  ]

  const questions = [
    'Are you licensed and insured in Kansas?',
    'Can I see recent Overland Park references?',
    'What does your inspection include?',
    'Do you provide photo documentation?',
    'How do you protect my property during work?',
    'What is your warranty on workmanship?',
    'What manufacturer warranties come with materials?',
    'What is the project timeline?',
    'Do you handle permits?',
    'What financing options do you offer?'
  ]

  const redFlags = [
    { flag: 'Pressure to sign today', why: 'Quality contractors respect your decision timeline' },
    { flag: 'No written estimate', why: 'Everything should be documented and clear' },
    { flag: 'Vague scope of work', why: 'You should know exactly what is included' },
    { flag: 'No photo documentation offered', why: 'Photos prove condition and work quality' },
    { flag: 'Cash-only or full payment upfront', why: 'Normal payment schedules protect both parties' },
    { flag: 'No local references', why: 'Established contractors have trackable local work' },
    { flag: 'No mention of site cleanup', why: 'Professional contractors protect and clean your property' },
    { flag: 'Unlicensed or uninsured', why: 'Puts you at legal and financial risk' }
  ]

  const teamworkMatch = [
    { promise: 'Licensed & Insured', match: 'Fully licensed and insured to work in Kansas' },
    { promise: 'Same-Week Inspections', match: 'We schedule within the same week you call' },
    { promise: 'Photo Documentation', match: 'Every inspection includes detailed photos' },
    { promise: 'Clean Site Guarantee', match: 'Tarps, daily cleanup, magnetic nail sweeps, final walkthrough' },
    { promise: 'Clear Communication', match: 'Photos, written scope, honest options, no pressure' },
    { promise: 'Teamwork Financing', match: 'Flexible payment plans available' },
    { promise: 'Teamwork Warranty', match: 'Workmanship warranty backed by our partnership commitment' }
  ]

  return (
    <>
      <div className="bg-white border-b border-light-border">
        <div className="container-custom py-4">
          <div className="flex items-center space-x-2 text-sm text-text-muted">
            <Link href="/" className="hover:text-teamwork-green">Home</Link>
            <span>/</span>
            <Link href="/overland-park-ks/" className="hover:text-teamwork-green">Overland Park</Link>
            <span>/</span>
            <span className="text-text-secondary">Roofing Companies Guide</span>
          </div>
        </div>
      </div>

      <section className="section-padding bg-light-bg">
        <div className="container-custom">
          <div className="max-w-3xl mx-auto">
            <h1 className="heading-1 mb-6">
              How to Choose a Roofing Company in <span className="text-teamwork-green">Overland Park</span>
            </h1>
            <p className="text-xl text-text-secondary mb-8">
              Your roof is a major investment. Use this checklist to make an informed decision and avoid common pitfalls when hiring a roofing company in Overland Park.
            </p>
            <div className="flex flex-wrap gap-4">
              <Link href="/book/" className="btn-primary">Book Inspection</Link>
              <Link href="/estimate/" className="btn-secondary">Get Estimate</Link>
            </div>
          </div>
        </div>
      </section>

      <section className="section-padding bg-white">
        <div className="container-custom">
          <h2 className="heading-2 mb-12 text-center">Overland Park Roofing Company Checklist</h2>
          <div className="max-w-3xl mx-auto">
            <p className="text-text-secondary mb-8 text-center">Look for these when choosing a roofing contractor:</p>
            <div className="grid md:grid-cols-2 gap-4">
              {checklist.map((item, index) => (
                <div key={index} className="flex items-start space-x-3">
                  <FiCheckCircle className="w-5 h-5 text-teamwork-green mt-1 flex-shrink-0" />
                  <div>
                    <span className="text-text-secondary">{item}</span>
                    {item === 'Emergency/urgent service availability' && (
                      <p className="text-xs text-text-muted mt-1">
                        If you need urgent help, see <Link href="/overland-park-ks/emergency-roof-repair/" className="text-teamwork-green hover:underline">Emergency Roof Repair in Overland Park →</Link>
                      </p>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </section>

      <section className="section-padding bg-light-bg">
        <div className="container-custom">
          <h2 className="heading-2 mb-12 text-center">Questions to Ask Before Signing</h2>
          <div className="max-w-3xl mx-auto space-y-3">
            {questions.map((question, index) => (
              <div key={index} className="card">
                <p className="font-semibold text-text-primary">{index + 1}. {question}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      <section className="section-padding bg-white">
        <div className="container-custom">
          <h2 className="heading-2 mb-12 text-center">Red Flags to Avoid</h2>
          <div className="max-w-4xl mx-auto grid md:grid-cols-2 gap-6">
            {redFlags.map((item, index) => (
              <div key={index} className="card border-red-500/20">
                <div className="flex items-start space-x-3 mb-2">
                  <FiX className="w-5 h-5 text-red-500 mt-1 flex-shrink-0" />
                  <h4 className="font-semibold text-red-400">{item.flag}</h4>
                </div>
                <p className="text-sm text-text-secondary ml-8">{item.why}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      <section className="section-padding bg-light-bg">
        <div className="container-custom">
          <h2 className="heading-2 mb-12 text-center">How Teamwork Matches the Checklist</h2>
          <div className="max-w-3xl mx-auto space-y-4">
            {teamworkMatch.map((item, index) => (
              <div key={index} className="card">
                <div className="flex items-start space-x-3">
                  <FiCheckCircle className="w-5 h-5 text-teamwork-green mt-1 flex-shrink-0" />
                  <div>
                    <h4 className="font-semibold mb-1">{item.promise}</h4>
                    <p className="text-sm text-text-secondary">{item.match}</p>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      <LocalProjectsSection city="Overland Park" />

      <section className="section-padding bg-white">
        <div className="container-custom">
          <div className="card max-w-3xl mx-auto bg-yellow-500/5 border-yellow-500">
            <div className="flex items-start space-x-3 mb-4">
              <FiAlertTriangle className="w-6 h-6 text-yellow-500 mt-1 flex-shrink-0" />
              <div>
                <h3 className="heading-4 mb-2">Final Tip: Trust Your Gut</h3>
                <p className="text-text-secondary mb-3">
                  Beyond checklists and questions, pay attention to how a roofing company makes you feel.
                </p>
                <ul className="space-y-2 text-sm text-text-secondary">
                  <li>Do they listen to your concerns?</li>
                  <li>Do they answer questions clearly?</li>
                  <li>Do they respect your timeline?</li>
                  <li>Do they seem trustworthy?</li>
                </ul>
                <p className="text-text-secondary mt-3">
                  At Teamwork, we believe the relationship matters as much as the roof itself.
                </p>
              </div>
            </div>
          </div>
        </div>
      </section>

      <CTABand title="Ready to Experience the Teamwork Difference?" subtitle="Book your same-week inspection in Overland Park" />
    </>
  )
}
