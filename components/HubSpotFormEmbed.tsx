'use client'

import { useEffect, useRef } from 'react'
import { usePathname } from 'next/navigation'

interface HubSpotFormEmbedProps {
  formId: string
  title?: string
  subtitle?: string
  onSubmit?: () => void
}

/**
 * HubSpot Form Embed Component
 * Loads and renders HubSpot forms with automatic hidden field injection
 *
 * Hidden fields automatically added:
 * - page_url: Current page URL
 * - page_path: Current route path
 * - city: Detected from route (e.g., /overland-park-ks/ => "Overland Park, KS")
 * - service_interest: Detected from page type
 * - lead_source: Always "Website"
 */
export default function HubSpotFormEmbed({ formId, title, subtitle, onSubmit }: HubSpotFormEmbedProps) {
  const formContainer = useRef<HTMLDivElement>(null)
  const pathname = usePathname()
  const portalId = process.env.NEXT_PUBLIC_HUBSPOT_PORTAL_ID || '244741088'
  const region = process.env.NEXT_PUBLIC_HUBSPOT_REGION || 'na2'

  // Detect city from pathname
  const getCity = (): string => {
    if (pathname.includes('overland-park-ks')) return 'Overland Park, KS'
    if (pathname.includes('leawood-ks')) return 'Leawood, KS'
    if (pathname.includes('lenexa-ks')) return 'Lenexa, KS'
    return 'Kansas City Metro'
  }

  // Detect service interest from pathname
  const getServiceInterest = (): string => {
    if (pathname.includes('roof-replacement')) return 'Roof Replacement'
    if (pathname.includes('roof-repair')) return 'Roof Repair'
    if (pathname.includes('storm')) return 'Storm Damage'
    if (pathname.includes('gutters')) return 'Gutters'
    if (pathname.includes('siding')) return 'Siding'
    if (pathname.includes('windows')) return 'Windows'
    if (pathname.includes('estimate')) return 'Estimate Request'
    if (pathname.includes('book')) return 'Inspection Request'
    return 'General Inquiry'
  }

  useEffect(() => {
    // Load HubSpot forms script if not already loaded
    if (typeof window !== 'undefined' && !(window as any).hbspt) {
      const script = document.createElement('script')
      script.src = `https://js-${region}.hsforms.net/forms/embed/v2.js`
      script.async = true
      script.defer = true
      document.body.appendChild(script)

      script.onload = () => {
        createForm()
      }
    } else if ((window as any).hbspt) {
      createForm()
    }

    function createForm() {
      if ((window as any).hbspt && formContainer.current) {
        ;(window as any).hbspt.forms.create({
          region,
          portalId,
          formId,
          target: `#hubspot-form-${formId}`,
          onFormReady: ($form: any) => {
            // Apply Tailwind styling to form elements
            const form = $form[0]
            if (form) {
              // Style all inputs
              const inputs = form.querySelectorAll('input[type="text"], input[type="tel"], input[type="email"], textarea, select')
              inputs.forEach((input: HTMLElement) => {
                input.classList.add(
                  'w-full', 'px-4', 'py-3', 'bg-light-bg', 'border', 'border-light-border',
                  'rounded-lg', 'focus:border-teamwork-blue', 'focus:ring-2',
                  'focus:ring-teamwork-blue/20', 'focus:outline-none', 'transition-all', 'duration-200'
                )
              })

              // Style submit button
              const submitBtn = form.querySelector('input[type="submit"]')
              if (submitBtn) {
                submitBtn.classList.add(
                  'btn-primary', 'w-full', 'hover:scale-105', 'active:scale-95',
                  'transition-transform', 'duration-200', '!bg-teamwork-blue', '!text-white'
                )
              }

              // Style labels
              const labels = form.querySelectorAll('label')
              labels.forEach((label: HTMLElement) => {
                label.classList.add('block', 'text-sm', 'font-semibold', 'mb-2')
              })
            }
          },
          onFormSubmit: () => {
            if (onSubmit) {
              onSubmit()
            }
          },
          // Hidden fields with context data
          onBeforeFormSubmit: ($form: any) => {
            // These will be injected if the fields exist in HubSpot form
            const hiddenFields = {
              page_url: typeof window !== 'undefined' ? window.location.href : '',
              page_path: pathname,
              city: getCity(),
              service_interest: getServiceInterest(),
              lead_source: 'Website'
            }

            // Try to set hidden fields if they exist
            Object.entries(hiddenFields).forEach(([key, value]) => {
              const field = $form[0]?.querySelector(`input[name="${key}"]`)
              if (field) {
                field.value = value
              }
            })
          }
        })
      }
    }
  }, [formId, pathname, portalId, region, onSubmit])

  return (
    <div>
      {(title || subtitle) && (
        <div className="mb-6">
          {title && <h3 className="heading-4 mb-2">{title}</h3>}
          {subtitle && <p className="text-text-secondary">{subtitle}</p>}
        </div>
      )}
      <div id={`hubspot-form-${formId}`} ref={formContainer} />
    </div>
  )
}
