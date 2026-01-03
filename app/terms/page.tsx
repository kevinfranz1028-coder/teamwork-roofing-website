export const metadata = {
  title: 'Terms of Service | Teamwork Roofing Services',
  description: 'Terms of service for Teamwork Roofing Services LLC',
}

export default function TermsPage() {
  return (
    <section className="section-padding bg-light-bg">
      <div className="container-custom max-w-4xl">
        <h1 className="heading-1 mb-8">Terms of Service</h1>

        <div className="space-y-6 text-text-secondary">
          <p className="text-sm text-text-muted">Last updated: {new Date().toLocaleDateString()}</p>

          <div>
            <h2 className="heading-4 text-text-primary mb-3">Agreement to Terms</h2>
            <p>
              By using the Teamwork Roofing Services LLC website, requesting estimates, or booking inspections,
              you agree to these terms of service.
            </p>
          </div>

          <div>
            <h2 className="heading-4 text-text-primary mb-3">Services</h2>
            <p>
              Teamwork Roofing Services LLC provides roofing, gutter, siding, and window services in the Kansas City Metro area.
              Estimates are approximations and final pricing may vary based on actual scope of work discovered during inspection.
            </p>
          </div>

          <div>
            <h2 className="heading-4 text-text-primary mb-3">Estimates and Pricing</h2>
            <p>
              Online estimates are starting-point approximations only. Final pricing requires an in-person inspection.
              We reserve the right to adjust pricing based on actual conditions, scope changes, or unforeseen issues.
            </p>
          </div>

          <div>
            <h2 className="heading-4 text-text-primary mb-3">Scheduling and Inspections</h2>
            <p>
              While we promise same-week inspection scheduling, specific dates and times are subject to availability
              and weather conditions. Emergency situations receive priority scheduling.
            </p>
          </div>

          <div>
            <h2 className="heading-4 text-text-primary mb-3">Warranty Disclaimer</h2>
            <p>
              Our Teamwork Warranty covers installation workmanship as described on our Warranty page. It does not cover
              storm damage, neglect, normal wear, or work performed by other contractors. See our full Warranty page for details.
            </p>
          </div>

          <div>
            <h2 className="heading-4 text-text-primary mb-3">Insurance Claims</h2>
            <p>
              We provide documentation to support insurance claims but do not guarantee claim approval or outcomes.
              Insurance claim decisions are made solely by your insurance company.
            </p>
          </div>

          <div>
            <h2 className="heading-4 text-text-primary mb-3">Website Use</h2>
            <p>
              Content on this website is for informational purposes. We reserve the right to modify website content,
              services, and pricing at any time without notice.
            </p>
          </div>

          <div>
            <h2 className="heading-4 text-text-primary mb-3">Limitation of Liability</h2>
            <p>
              Teamwork Roofing Services LLC is not liable for indirect, incidental, or consequential damages arising
              from our services or website use.
            </p>
          </div>

          <div>
            <h2 className="heading-4 text-text-primary mb-3">Contact</h2>
            <p>
              For questions about these terms, contact us at:
            </p>
            <p className="mt-2">
              Teamwork Roofing Services LLC<br />
              Phone: <a href="tel:9133963717" className="text-teamwork-blue hover:underline">913-396-3717</a>
            </p>
          </div>
        </div>
      </div>
    </section>
  )
}
