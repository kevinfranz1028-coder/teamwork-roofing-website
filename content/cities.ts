export interface CityData {
  slug: string
  cityName: string
  state: string
  phone: string
  hub: {
    h1: string
    intro: string
  }
  neighborhoods: string[]
  localProof: {
    title: string
    bullets: string[]
    disclaimer: string
  }
  reviews: Array<{
    name: string
    city: string
    rating: number
    text: string
  }>
  faqs: Array<{
    q: string
    a: string
    link?: {
      text: string
      href: string
    }
  }>
}

export const cities: Record<string, CityData> = {
  'leawood-ks': {
    slug: 'leawood-ks',
    cityName: 'Leawood',
    state: 'KS',
    phone: '913-396-3717',
    hub: {
      h1: 'Roofing & Exteriors in Leawood, KS — Done The Teamwork Way',
      intro: 'A partnership from day one. Teamwork provides roof repair, roof replacement, and storm inspections in Leawood — backed by photo-proof documentation, clean site practices, flexible financing, and a Teamwork Warranty.'
    },
    neighborhoods: [
      'Old Leawood',
      'Leawood Estates',
      'Hallbrook',
      'Mission Farms',
      'Pattee Creek',
      'Leawood South',
      'Highlands Creek',
      'Berkshire',
      'Oxford Hills',
      'Deer Creek (Leawood area)',
      'Tomahawk Creek area',
      '119th & Roe area'
    ],
    localProof: {
      title: 'Permits & HOA Awareness in Leawood',
      bullets: [
        'Leawood reroofs often require a permit — we\'ll confirm what applies during your inspection.',
        'If HOA notifications apply, we\'ll help you stay organized with timing and documentation.',
        'We follow local requirements and keep the process simple.'
      ],
      disclaimer: 'Requirements vary by project; we\'ll confirm what applies during inspection.'
    },
    reviews: [
      {
        name: 'Michael T.',
        city: 'Leawood',
        rating: 5,
        text: 'Outstanding service from start to finish. They handled our HOA requirements seamlessly and the cleanup was impeccable.'
      },
      {
        name: 'Patricia S.',
        city: 'Leawood',
        rating: 5,
        text: 'Professional team that respected our property. Photo documentation made the entire process transparent and easy to follow.'
      },
      {
        name: 'James W.',
        city: 'Leawood',
        rating: 5,
        text: 'Same-week inspection delivered as promised. Clear pricing, expert installation, and beautiful results on our Hallbrook home.'
      }
    ],
    faqs: [
      {
        q: 'Do you serve all of Leawood?',
        a: 'Yes — we serve homeowners across all of Leawood, including Old Leawood, Hallbrook, Mission Farms, Leawood Estates, and surrounding neighborhoods.'
      },
      {
        q: 'How fast can you inspect my roof in Leawood?',
        a: 'We promise same-week inspections. Most Leawood inspections are scheduled within 1-3 days of your call.'
      },
      {
        q: 'Do you provide photo documentation?',
        a: 'Yes, every inspection includes detailed photos so you can see exactly what we see. Full transparency.'
      },
      {
        q: 'Can you help with Leawood permit requirements?',
        a: 'Yes. We\'ll confirm what permits apply to your project and handle the process. Requirements vary by project — we make it simple.'
      },
      {
        q: 'Do you work with HOA requirements in Leawood?',
        a: 'Yes. Many Leawood neighborhoods have HOA guidelines. We\'ll help you navigate notifications and documentation to stay organized.'
      },
      {
        q: 'Can you inspect my roof after hail or wind storms in Leawood?',
        a: 'Yes. We offer same-week storm inspections with professional photo documentation and a clear scope of recommended repairs.',
        link: { text: 'storm inspections', href: '/storm/' }
      },
      {
        q: 'Do you offer emergency roof leak help in Leawood?',
        a: 'Yes. If you have an active leak, call or text us right now. We will help you take the next best step and schedule an urgent inspection.',
        link: { text: 'emergency roof leak help', href: '/leawood-ks/emergency-roof-repair/' }
      },
      {
        q: 'Are you licensed and insured in Kansas?',
        a: 'Yes, we are fully licensed and insured to work throughout Kansas including Leawood and Johnson County.'
      },
      {
        q: 'Do you offer financing?',
        a: 'Yes, we offer Teamwork Financing options with flexible terms to fit your budget.',
        link: { text: 'Teamwork Financing', href: '/financing/' }
      },
      {
        q: 'What is your warranty?',
        a: 'Our Teamwork Warranty covers installation workmanship, plus manufacturer warranties on materials (25 years to lifetime depending on product).',
        link: { text: 'Teamwork Warranty', href: '/warranty/' }
      }
    ]
  },
  'lenexa-ks': {
    slug: 'lenexa-ks',
    cityName: 'Lenexa',
    state: 'KS',
    phone: '913-396-3717',
    hub: {
      h1: 'Roofing & Exteriors in Lenexa, KS — Done The Teamwork Way',
      intro: 'A partnership from day one. Teamwork provides roof repair, roof replacement, and storm inspections in Lenexa — backed by photo-proof documentation, clean site practices, flexible financing, and a Teamwork Warranty.'
    },
    neighborhoods: [
      'Old Town Lenexa',
      'Lenexa Hills',
      'Falcon Valley',
      'The Reserve',
      'Canyon Creek',
      'Grey Oaks',
      'Woodland Reserve',
      'Black Hoof Park area',
      'Parkhurst',
      'Westchester',
      '87th & Lackman area',
      'K-10 corridor area'
    ],
    localProof: {
      title: 'Built for Lenexa Requirements',
      bullets: [
        'We install underlayment and ice/water protection as required for your project.',
        'We schedule inspections when required and keep the process simple.',
        'We document scope clearly so you can decide fast.'
      ],
      disclaimer: 'Requirements vary by project; we\'ll confirm what applies during inspection.'
    },
    reviews: [
      {
        name: 'Karen L.',
        city: 'Lenexa',
        rating: 5,
        text: 'Excellent communication throughout. They arrived on time, worked efficiently, and left our property spotless.'
      },
      {
        name: 'Robert D.',
        city: 'Lenexa',
        rating: 5,
        text: 'True professionals. The photo documentation helped us make an informed decision, and the installation was flawless.'
      },
      {
        name: 'Linda M.',
        city: 'Lenexa',
        rating: 5,
        text: 'Same-week inspection made all the difference. Fair pricing, quality work, and they honored every commitment.'
      }
    ],
    faqs: [
      {
        q: 'Do you serve all of Lenexa?',
        a: 'Yes — we serve homeowners across all of Lenexa, including Old Town, Lenexa Hills, Falcon Valley, Canyon Creek, and surrounding neighborhoods.'
      },
      {
        q: 'How fast can you inspect my roof in Lenexa?',
        a: 'We promise same-week inspections. Most Lenexa inspections are scheduled within 1-3 days of your call.'
      },
      {
        q: 'Do you provide photo documentation?',
        a: 'Yes, every inspection includes detailed photos so you can see exactly what we see. Full transparency.'
      },
      {
        q: 'Can you inspect my roof after hail or wind storms in Lenexa?',
        a: 'Yes. We offer same-week storm inspections with professional photo documentation and a clear scope of recommended repairs.',
        link: { text: 'storm inspections', href: '/storm/' }
      },
      {
        q: 'Do you offer emergency roof leak help in Lenexa?',
        a: 'Yes. If you have an active leak, call or text us right now. We will help you take the next best step and schedule an urgent inspection.',
        link: { text: 'emergency roof leak help', href: '/lenexa-ks/emergency-roof-repair/' }
      },
      {
        q: 'Are you licensed and insured in Kansas?',
        a: 'Yes, we are fully licensed and insured to work throughout Kansas including Lenexa and Johnson County.'
      },
      {
        q: 'Do you offer financing?',
        a: 'Yes, we offer Teamwork Financing options with flexible terms to fit your budget.',
        link: { text: 'Teamwork Financing', href: '/financing/' }
      },
      {
        q: 'What is your warranty?',
        a: 'Our Teamwork Warranty covers installation workmanship, plus manufacturer warranties on materials (25 years to lifetime depending on product).',
        link: { text: 'Teamwork Warranty', href: '/warranty/' }
      }
    ]
  }
}
