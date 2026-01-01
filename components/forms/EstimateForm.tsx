'use client'

import HubSpotFormEmbed from '../HubSpotFormEmbed'

export default function EstimateForm() {
  const formId = process.env.NEXT_PUBLIC_HUBSPOT_FORM_ID_ESTIMATE || 'REPLACE_ME'

  return (
    <div className="card max-w-2xl mx-auto">
      <HubSpotFormEmbed
        formId={formId}
        title="Book Your Same-Week Inspection"
        subtitle="Provide your contact info and we'll reach out to schedule your inspection"
      />
    </div>
  )
}
