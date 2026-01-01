'use client'

import { useState } from 'react'
import { FiCheckCircle } from 'react-icons/fi'
import HubSpotFormEmbed from '../HubSpotFormEmbed'

export default function BookInspectionForm() {
  const [submitted, setSubmitted] = useState(false)
  const formId = process.env.NEXT_PUBLIC_HUBSPOT_FORM_ID_BOOK || 'REPLACE_ME'

  const handleSubmit = () => {
    setSubmitted(true)
    // Reset after 3 seconds
    setTimeout(() => setSubmitted(false), 3000)
  }

  if (submitted) {
    return (
      <div className="card max-w-2xl text-center">
        <div className="w-20 h-20 rounded-full bg-green-500/10 flex items-center justify-center mx-auto mb-6">
          <FiCheckCircle className="w-10 h-10 text-green-500" />
        </div>
        <h2 className="heading-2 mb-4">Inspection Requested!</h2>
        <p className="text-xl text-text-secondary mb-6">
          Thank you for choosing Teamwork Roofing. We'll contact you within 24 hours to confirm your same-week inspection.
        </p>
        <p className="text-text-muted">
          Questions? Call us at <a href="tel:9133963717" className="text-teamwork-blue hover:underline">913-396-3717</a>
        </p>
      </div>
    )
  }

  return (
    <div className="card">
      <HubSpotFormEmbed
        formId={formId}
        title="Inspection Request Form"
        onSubmit={handleSubmit}
      />
    </div>
  )
}
