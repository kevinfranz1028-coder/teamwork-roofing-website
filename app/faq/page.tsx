'use client'

import { useState } from 'react'
import { FiChevronDown } from 'react-icons/fi'
import CTABand from '@/components/CTABand'

export default function FAQPage() {
  const [openCategory, setOpenCategory] = useState<string | null>('general')
  const [openQuestion, setOpenQuestion] = useState<number | null>(null)

  const categories = [
    {
      id: 'general',
      title: 'General',
      faqs: [
        { q: 'Do you really inspect same-week?', a: 'Yes — it\'s our promise. We schedule inspections within the same week you contact us, often within 1-3 days.' },
        { q: 'What areas do you serve?', a: 'Kansas City Metro including KCK, KCMO, Johnson County, Wyandotte County, Jackson County, and nearby areas in Kansas and Missouri.' },
        { q: 'Are you licensed and insured?', a: 'Yes, we are fully licensed and insured for your protection and peace of mind.' },
        { q: 'What does photo-proof inspection mean?', a: 'We document everything with detailed photos so you can see exactly what we see — full transparency on every project.' },
        { q: 'What is the clean site guarantee?', a: 'We protect your property during work with tarps, careful material handling, magnetic sweeps for nails, and thorough cleanup when we\'re done.' }
      ]
    },
    {
      id: 'roof-replacement',
      title: 'Roof Replacement',
      faqs: [
        { q: 'How long does a roof replacement take?', a: 'Most residential roof replacements take 1-3 days, depending on size, complexity, and weather.' },
        { q: 'Do you handle permits?', a: 'Yes, we handle all necessary permits as part of our service.' },
        { q: 'What warranty do you offer on roof replacement?', a: 'Manufacturer warranties range from 25 years to lifetime depending on materials. Plus our Teamwork Warranty on installation workmanship.' },
        { q: 'Can I stay home during roof replacement?', a: 'Yes, though it will be loud. Many homeowners choose to stay, some prefer to leave for the day.' },
        { q: 'What if it rains during my roof replacement?', a: 'We monitor weather closely and protect your home with tarps if unexpected rain occurs. We won\'t leave your home exposed.' }
      ]
    },
    {
      id: 'roof-repair',
      title: 'Roof Repair',
      faqs: [
        { q: 'How do I know if I need repair or replacement?', a: 'We\'ll assess your roof honestly and show you photos. If repair makes sense, we\'ll repair it. If replacement is smarter long-term, we\'ll explain why.' },
        { q: 'Do you offer emergency roof repair?', a: 'Yes, call 913-396-3717 for active leaks or emergency situations. We prioritize urgent repairs.' },
        { q: 'How long do roof repairs last?', a: 'Depends on the repair type and roof age. Quality repairs on newer roofs can last years; older roofs may need replacement soon.' },
        { q: 'Will my repair be covered by warranty?', a: 'Yes, our repair work is backed by our Teamwork Warranty.' }
      ]
    },
    {
      id: 'storm-insurance',
      title: 'Storm / Insurance',
      faqs: [
        { q: 'Do you help with insurance claims?', a: 'We provide detailed photo documentation and a written scope of damage you can share with your insurer and adjuster. We are not public adjusters and do not negotiate or settle claims.' },
        { q: 'Can Teamwork negotiate with my insurance company for me?', a: 'No. Kansas and Missouri have rules about who can negotiate or represent an insured on a claim. We focus on inspection, photos, and a clear repair scope you can share with your insurer/adjuster. If you want claim representation, consider a licensed public adjuster or an attorney.' },
        { q: 'Should I call my insurance first or you first?', a: 'Call your insurance to file the claim, then call us for a professional inspection and documentation.' },
        { q: 'What does a storm inspection include?', a: 'We inspect your entire exterior: roof, gutters, siding, and windows for storm-related damage and provide photo documentation.' },
        { q: 'Can you be on-site during the adjuster visit?', a: 'Yes, at your request we can be present during the adjuster inspection to answer construction questions about materials, code-related items, and repair methods.' },
        { q: 'Do I have to use my insurance company\'s contractor?', a: 'No, you have the right to choose your own contractor. Your insurance must pay fair market rates for the work.' }
      ]
    },
    {
      id: 'gutters',
      title: 'Gutters',
      faqs: [
        { q: 'What size gutters do I need?', a: 'Most homes use 5" gutters. Larger homes or steep roofs may benefit from 6" gutters. We\'ll recommend based on your home.' },
        { q: 'Are gutter guards worth it?', a: 'For most homeowners, yes. They reduce maintenance, prevent clogs, and protect your gutter investment.' },
        { q: 'How long do seamless gutters last?', a: 'Quality seamless aluminum gutters typically last 20-30 years with proper maintenance.' }
      ]
    },
    {
      id: 'siding',
      title: 'Siding',
      faqs: [
        { q: 'What siding material is best?', a: 'Depends on your budget and preferences. Vinyl is affordable and low-maintenance. Fiber cement is premium and durable. We\'ll explain all options.' },
        { q: 'Can you match my existing siding?', a: 'Often yes, but depends on age and availability. We\'ll do our best to find a match or recommend complementary options.' },
        { q: 'How long does siding installation take?', a: 'Depends on home size and complexity. Most residential siding projects take 3-7 days.' }
      ]
    },
    {
      id: 'windows',
      title: 'Windows',
      faqs: [
        { q: 'How much can new windows save on energy bills?', a: 'Typically 10-25% depending on your current windows and home. Modern windows are significantly more efficient.' },
        { q: 'Do you offer different window styles?', a: 'Yes, including double-hung, casement, slider, bay, and more. We\'ll help you choose the right style for each location.' },
        { q: 'Is financing available for window replacement?', a: 'Yes, we offer Teamwork Financing options to fit your budget.' }
      ]
    },
    {
      id: 'financing',
      title: 'Financing',
      faqs: [
        { q: 'What financing options are available?', a: 'We offer flexible Teamwork Financing options with various terms. Details provided during your estimate.' },
        { q: 'Do I need good credit?', a: 'Multiple options are available for various credit profiles. We\'ll help you find a solution.' },
        { q: 'How fast is financing approval?', a: 'Often same-day or next-day decisions.' },
        { q: 'Are there financing fees?', a: 'We\'ll explain all terms upfront — no surprises.' }
      ]
    },
    {
      id: 'warranty',
      title: 'Warranty',
      faqs: [
        { q: 'What does the Teamwork Warranty cover?', a: 'Our installation workmanship, leak-free performance, and clean site practices. See our Warranty page for full details.' },
        { q: 'How long is the warranty?', a: 'Installation workmanship warranty terms vary by project type. Manufacturer material warranties range from 25 years to lifetime.' },
        { q: 'How do I file a warranty claim?', a: 'Call us at 913-396-3717 or use our contact form. We\'ll schedule an inspection and address covered issues promptly.' }
      ]
    }
  ]

  return (
    <>
      <section className="section-padding bg-dark-bg">
        <div className="container-custom">
          <div className="text-center mb-12">
            <h1 className="heading-1 mb-6">Frequently Asked Questions</h1>
            <p className="text-xl text-gray-400">
              Find answers to common questions about our services
            </p>
          </div>

          <div className="max-w-4xl mx-auto">
            {/* Category Buttons */}
            <div className="flex flex-wrap gap-3 mb-8 justify-center">
              {categories.map((category) => (
                <button
                  key={category.id}
                  onClick={() => {
                    setOpenCategory(openCategory === category.id ? null : category.id)
                    setOpenQuestion(null)
                  }}
                  className={`px-4 py-2 rounded-lg font-semibold transition-all ${
                    openCategory === category.id
                      ? 'bg-teamwork-blue text-white'
                      : 'bg-dark-surface text-gray-400 hover:text-white border border-dark-border'
                  }`}
                >
                  {category.title}
                </button>
              ))}
            </div>

            {/* FAQ Accordion */}
            <div className="space-y-3">
              {categories
                .filter((cat) => openCategory === cat.id)
                .map((category) =>
                  category.faqs.map((faq, index) => {
                    const isOpen = openQuestion === index
                    return (
                      <div key={index} className="card">
                        <button
                          onClick={() => setOpenQuestion(isOpen ? null : index)}
                          className="w-full flex items-center justify-between text-left"
                        >
                          <h4 className="font-semibold pr-4">{faq.q}</h4>
                          <FiChevronDown
                            className={`w-5 h-5 text-teamwork-blue flex-shrink-0 transition-transform ${
                              isOpen ? 'rotate-180' : ''
                            }`}
                          />
                        </button>
                        {isOpen && <p className="text-gray-400 text-sm mt-3 pt-3 border-t border-dark-border">{faq.a}</p>}
                      </div>
                    )
                  })
                )}
            </div>

            {!openCategory && (
              <div className="text-center py-12">
                <p className="text-gray-500">Select a category above to view questions</p>
              </div>
            )}
          </div>
        </div>
      </section>

      <CTABand title="Still Have Questions?" subtitle="Call us at 913-396-3717 or book your same-week inspection" />
    </>
  )
}
