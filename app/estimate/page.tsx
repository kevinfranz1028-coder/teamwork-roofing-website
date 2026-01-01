'use client'

import { useState } from 'react'
import Link from 'next/link'
import { FiHome, FiDroplet, FiLayers, FiSquare, FiCloudRain } from 'react-icons/fi'
import PromiseStrip from '@/components/PromiseStrip'
import EstimateForm from '@/components/forms/EstimateForm'

export default function EstimatePage() {
  const [step, setStep] = useState<'service' | 'questions' | 'result'>('service')
  const [selectedService, setSelectedService] = useState('')
  const [formData, setFormData] = useState({
    size: '',
    stories: '',
    urgency: ''
  })
  const [estimatedPrice, setEstimatedPrice] = useState(0)

  const services = [
    { id: 'roofing', icon: FiHome, title: 'Roofing', color: 'blue' },
    { id: 'gutters', icon: FiDroplet, title: 'Gutters', color: 'cyan' },
    { id: 'siding', icon: FiLayers, title: 'Siding', color: 'green' },
    { id: 'windows', icon: FiSquare, title: 'Windows', color: 'purple' },
    { id: 'storm', icon: FiCloudRain, title: 'Storm/Full Exterior', color: 'orange' }
  ]

  const handleServiceSelect = (serviceId: string) => {
    setSelectedService(serviceId)
    setStep('questions')
  }

  const handleQuestionsSubmit = () => {
    // Simple estimation logic
    let basePrice = 0

    if (selectedService === 'roofing') {
      const sizeMultiplier = formData.size === 'small' ? 8000 : formData.size === 'medium' ? 12000 : 16000
      const storiesMultiplier = formData.stories === '1' ? 1 : formData.stories === '2' ? 1.3 : 1.5
      basePrice = sizeMultiplier * storiesMultiplier
    } else if (selectedService === 'gutters') {
      basePrice = formData.size === 'small' ? 1500 : formData.size === 'medium' ? 2200 : 3000
    } else if (selectedService === 'siding') {
      basePrice = formData.size === 'small' ? 12000 : formData.size === 'medium' ? 18000 : 25000
    } else if (selectedService === 'windows') {
      basePrice = 8000
    } else if (selectedService === 'storm') {
      basePrice = 15000
    }

    setEstimatedPrice(Math.round(basePrice))
    setStep('result')
  }

  return (
    <>
      <section className="section-padding bg-light-bg min-h-screen">
        <div className="container-custom max-w-4xl">
          {/* Header */}
          <div className="text-center mb-12">
            <h1 className="heading-1 mb-4">Start Your Teamwork Estimate</h1>
            <p className="text-xl text-text-secondary">
              Get a quick starting-at number, then book a same-week inspection for exact scope
            </p>
          </div>

          {/* Service Selection */}
          {step === 'service' && (
            <div className="space-y-8">
              <h2 className="heading-3 text-center mb-6">Select Your Service</h2>
              <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
                {services.map((service) => {
                  const Icon = service.icon
                  return (
                    <button
                      key={service.id}
                      onClick={() => handleServiceSelect(service.id)}
                      className="card hover:border-teamwork-blue transition-all duration-200 text-left group"
                    >
                      <Icon className="w-12 h-12 text-teamwork-blue mb-4 group-hover:scale-110 transition-transform" />
                      <h3 className="text-xl font-semibold">{service.title}</h3>
                    </button>
                  )
                })}
              </div>
            </div>
          )}

          {/* Questions */}
          {step === 'questions' && (
            <div className="card max-w-2xl mx-auto">
              <h2 className="heading-3 mb-6">Quick Details</h2>

              <div className="space-y-6">
                <div>
                  <label className="block text-sm font-semibold mb-2">Home Size</label>
                  <select
                    value={formData.size}
                    onChange={(e) => setFormData({ ...formData, size: e.target.value })}
                    className="w-full px-4 py-3 bg-light-bg border border-light-border rounded-lg focus:border-teamwork-blue focus:outline-none"
                    required
                  >
                    <option value="">Select size</option>
                    <option value="small">Small (Under 1,500 sq ft)</option>
                    <option value="medium">Medium (1,500 - 2,500 sq ft)</option>
                    <option value="large">Large (Over 2,500 sq ft)</option>
                  </select>
                </div>

                {selectedService === 'roofing' && (
                  <div>
                    <label className="block text-sm font-semibold mb-2">Number of Stories</label>
                    <select
                      value={formData.stories}
                      onChange={(e) => setFormData({ ...formData, stories: e.target.value })}
                      className="w-full px-4 py-3 bg-light-bg border border-light-border rounded-lg focus:border-teamwork-blue focus:outline-none"
                      required
                    >
                      <option value="">Select stories</option>
                      <option value="1">1 Story</option>
                      <option value="2">2 Stories</option>
                      <option value="3">3+ Stories</option>
                    </select>
                  </div>
                )}

                <div>
                  <label className="block text-sm font-semibold mb-2">Urgency</label>
                  <select
                    value={formData.urgency}
                    onChange={(e) => setFormData({ ...formData, urgency: e.target.value })}
                    className="w-full px-4 py-3 bg-light-bg border border-light-border rounded-lg focus:border-teamwork-blue focus:outline-none"
                    required
                  >
                    <option value="">Select urgency</option>
                    <option value="active-leak">Active Leak</option>
                    <option value="storm-damage">Storm Damage</option>
                    <option value="planning">Planning Ahead</option>
                    <option value="quote">Just Need Quote</option>
                  </select>
                </div>

                <div className="flex gap-4">
                  <button
                    onClick={() => setStep('service')}
                    className="btn-secondary flex-1"
                  >
                    Back
                  </button>
                  <button
                    onClick={handleQuestionsSubmit}
                    disabled={!formData.size || !formData.urgency}
                    className="btn-primary flex-1 disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    Get Estimate
                  </button>
                </div>
              </div>
            </div>
          )}

          {/* Result & HubSpot Form */}
          {step === 'result' && (
            <div className="space-y-8">
              {/* Estimate Result */}
              <div className="card text-center max-w-2xl mx-auto bg-gradient-to-br from-teamwork-blue to-blue-700">
                <h2 className="heading-3 mb-4">Your Estimated Starting Price</h2>
                <div className="text-6xl font-bold mb-4">
                  ${estimatedPrice.toLocaleString()}
                </div>
                <p className="text-blue-100 mb-6">
                  This is a starting estimate. Book your same-week inspection for exact pricing.
                </p>
              </div>

              {/* HubSpot Form */}
              <EstimateForm />

              {/* What Happens Next */}
              <div className="card max-w-2xl mx-auto">
                <h4 className="font-semibold mb-4">What Happens Next</h4>
                <ol className="space-y-3 text-text-secondary">
                  <li className="flex">
                    <span className="font-bold text-teamwork-blue mr-3">1.</span>
                    <span>We'll call or text within 24 hours</span>
                  </li>
                  <li className="flex">
                    <span className="font-bold text-teamwork-blue mr-3">2.</span>
                    <span>Schedule your same-week inspection</span>
                  </li>
                  <li className="flex">
                    <span className="font-bold text-teamwork-blue mr-3">3.</span>
                    <span>Receive photo documentation and exact pricing</span>
                  </li>
                  <li className="flex">
                    <span className="font-bold text-teamwork-blue mr-3">4.</span>
                    <span>Review options with our Teamwork Financing available</span>
                  </li>
                </ol>
              </div>
            </div>
          )}
        </div>
      </section>

      <PromiseStrip />
    </>
  )
}
