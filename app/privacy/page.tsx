export const metadata = {
  title: 'Privacy Policy | Teamwork Roofing Services',
  description: 'Privacy policy for Teamwork Roofing Services LLC',
}

export default function PrivacyPage() {
  return (
    <section className="section-padding bg-dark-bg">
      <div className="container-custom max-w-4xl">
        <h1 className="heading-1 mb-8">Privacy Policy</h1>

        <div className="space-y-6 text-gray-400">
          <p className="text-sm text-gray-500">Last updated: {new Date().toLocaleDateString()}</p>

          <div>
            <h2 className="heading-4 text-white mb-3">Information We Collect</h2>
            <p>
              When you contact Teamwork Roofing Services LLC, request an estimate, or book an inspection, we may collect:
            </p>
            <ul className="list-disc list-inside mt-2 space-y-1 ml-4">
              <li>Name and contact information (phone, email, address)</li>
              <li>Property details related to your service request</li>
              <li>Communication preferences</li>
              <li>Photos you provide of your property</li>
            </ul>
          </div>

          <div>
            <h2 className="heading-4 text-white mb-3">How We Use Your Information</h2>
            <p>We use your information to:</p>
            <ul className="list-disc list-inside mt-2 space-y-1 ml-4">
              <li>Schedule inspections and provide estimates</li>
              <li>Communicate about your project</li>
              <li>Send service updates and appointment reminders</li>
              <li>Improve our services</li>
            </ul>
          </div>

          <div>
            <h2 className="heading-4 text-white mb-3">Communication Consent</h2>
            <p>
              By providing your phone number, you consent to receive calls and text messages from Teamwork Roofing Services LLC
              regarding your service request, appointment reminders, and related communications. Message and data rates may apply.
              You can opt out at any time by texting STOP or contacting us directly.
            </p>
          </div>

          <div>
            <h2 className="heading-4 text-white mb-3">Information Sharing</h2>
            <p>
              We do not sell or rent your personal information. We may share information with service providers who help us
              operate our business (e.g., scheduling software, payment processors) under strict confidentiality agreements.
            </p>
          </div>

          <div>
            <h2 className="heading-4 text-white mb-3">Data Security</h2>
            <p>
              We implement reasonable security measures to protect your information. However, no method of transmission over
              the internet is 100% secure.
            </p>
          </div>

          <div>
            <h2 className="heading-4 text-white mb-3">Your Rights</h2>
            <p>You have the right to:</p>
            <ul className="list-disc list-inside mt-2 space-y-1 ml-4">
              <li>Request access to your personal information</li>
              <li>Request correction of inaccurate information</li>
              <li>Request deletion of your information</li>
              <li>Opt out of marketing communications</li>
            </ul>
          </div>

          <div>
            <h2 className="heading-4 text-white mb-3">Contact Us</h2>
            <p>
              For questions about this privacy policy or to exercise your rights, contact us at:
            </p>
            <p className="mt-2">
              Teamwork Roofing Services LLC<br />
              Phone: <a href="tel:9133963717" className="text-teamwork-blue hover:underline">913-396-3717</a>
            </p>
          </div>

          <div>
            <h2 className="heading-4 text-white mb-3">Changes to This Policy</h2>
            <p>
              We may update this privacy policy from time to time. Changes will be posted on this page with an updated date.
            </p>
          </div>
        </div>
      </div>
    </section>
  )
}
