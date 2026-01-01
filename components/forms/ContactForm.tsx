'use client'

import { useState } from 'react'
import { FiCheckCircle } from 'react-icons/fi'
import HubSpotFormEmbed from '../HubSpotFormEmbed'

export default function ContactForm() {
  const [submitted, setSubmitted] = useState(false)
  const formId = process.env.NEXT_PUBLIC_HUBSPOT_FORM_ID_CONTACT || 'REPLACE_ME'

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
        <h2 className="heading-2 mb-4">Message Sent!</h2>
        <p className="text-xl text-text-secondary">
          Thank you for contacting Teamwork Roofing. We'll respond within 24 hours.
        </p>
      </div>
    )
  }

  return (
    <div className="card">
      <HubSpotFormEmbed
        formId={formId}
        title="Send Us a Message"
        onSubmit={handleSubmit}
      />
    </div>
  )
}
