import approvals from './gallery-approvals.json'

export interface GalleryProject {
  id: string // Unique identifier (e.g., "op-001", "leawood-002")
  city: 'Overland Park' | 'Leawood' | 'Lenexa' | 'Kansas City' | 'Olathe' | 'Other'
  jobType: 'full-replacement' | 'storm-hail' | 'repair' | 'gutter' | 'siding' | 'inspection'
  beforeImage: string // Path to before photo (e.g., "/gallery/op-001/before.webp")
  afterImage?: string // Path to after photo (optional for inspection-only projects)
  beforeAlt: string // Descriptive alt text for before image
  afterAlt?: string // Descriptive alt text for after image (optional when afterImage is missing)
  description: string // Short description (e.g., "Full roof replacement after hail damage - GAF Timberline HD shingles")
  date: string // Completion date in YYYY-MM format (for sorting, not displayed)
  featured: boolean // Display on homepage?
  afterPending?: boolean // True when after photos will be added later (inspection-only projects)
  beforeCaption?: string // Custom caption for before image (overrides "Before")
  afterCaption?: string // Custom caption for after image (overrides "After")
  additionalImages?: string[] // Additional detail/supporting images
}

export interface GalleryApproval {
  approved: boolean
  approvedBy?: string
  approvedDate?: string
  blurChecked?: boolean
}

// ALL gallery projects (including unapproved placeholder entries)
// See docs/GALLERY.md for photo requirements and upload process
export const allGalleryProjects: GalleryProject[] = [
  // Kansas City, KS - Storm/hail roof project (HOMEPAGE HERO for now)
  {
    id: "kansas-city-ks-001",
    city: "Kansas City",
    jobType: "storm-hail",
    beforeImage: "/gallery/kansas-city-ks-001/kansas-city-ks-001-before-1.jpg",
    afterImage: "/gallery/kansas-city-ks-001/kansas-city-ks-001-after-1.jpg",
    beforeAlt: "Asphalt shingle roof during replacement work in Kansas City, KS",
    afterAlt: "Completed asphalt shingle roof in Kansas City, KS",
    beforeCaption: "During roof replacement",
    afterCaption: "Completed roof",
    description: "Storm damage roof replacement in Kansas City, KS",
    date: "2026-10",
    featured: true
  },
  // Kansas City, KS - Low-res storm/hail project (cap display at ~600px)
  {
    id: "kansas-city-ks-002",
    city: "Kansas City",
    jobType: "storm-hail",
    beforeImage: "/gallery/kansas-city-ks-002/kansas-city-ks-002-before-1.jpg",
    afterImage: "/gallery/kansas-city-ks-002/kansas-city-ks-002-after-1.jpg",
    beforeAlt: "Roof during replacement work in Kansas City, KS",
    afterAlt: "Completed roof in Kansas City, KS",
    beforeCaption: "During roof replacement",
    afterCaption: "Completed roof",
    description: "Storm damage roof replacement in Kansas City, KS",
    date: "2026-10",
    featured: false
  },
  // Olathe - Hail damage inspection (FEATURED, after photos pending)
  {
    id: "olathe-002",
    city: "Olathe",
    jobType: "inspection",
    beforeImage: "/gallery/olathe-002/olathe-002-before-1.jpg",
    beforeAlt: "Hail damage marked during roof inspection in Olathe",
    description: "Hail damage inspection in Olathe",
    date: "2026-11",
    featured: true,
    afterPending: true,
    additionalImages: [
      "/gallery/olathe-002/olathe-002-before-2.jpg",
      "/gallery/olathe-002/olathe-002-before-3.jpg",
      "/gallery/olathe-002/olathe-002-detail-3.jpg",
      "/gallery/olathe-002/olathe-002-detail-5.jpg",
      "/gallery/olathe-002/olathe-002-before-4.jpg",
      "/gallery/olathe-002/olathe-002-before-5.jpg",
      "/gallery/olathe-002/olathe-002-before-6.jpg",
      "/gallery/olathe-002/olathe-002-before-7.jpg",
      "/gallery/olathe-002/olathe-002-before-8.jpg",
      "/gallery/olathe-002/olathe-002-before-9.jpg",
      "/gallery/olathe-002/olathe-002-before-10.jpg",
      "/gallery/olathe-002/olathe-002-before-11.jpg",
      "/gallery/olathe-002/olathe-002-before-12.jpg",
      "/gallery/olathe-002/olathe-002-before-13.jpg",
      "/gallery/olathe-002/olathe-002-detail-1.jpg",
      "/gallery/olathe-002/olathe-002-detail-2.jpg",
      "/gallery/olathe-002/olathe-002-detail-4.jpg"
    ]
  },
  // Overland Park - Supporting shots
  {
    id: "overland-park-001",
    city: "Overland Park",
    jobType: "storm-hail",
    beforeImage: "/gallery/overland-park-001/overland-park-001-before-1.jpg",
    afterImage: "/gallery/overland-park-001/overland-park-001-after-1.jpg",
    beforeAlt: "Roof before work in Overland Park",
    afterAlt: "Completed roof in Overland Park",
    description: "Roof project in Overland Park",
    date: "2026-10",
    featured: false,
    additionalImages: [
      "/gallery/overland-park-001/overland-park-001-before-2.jpg",
      "/gallery/overland-park-001/overland-park-001-detail-1.jpg"
    ]
  }
]

/**
 * Get approval status for a project
 */
export function getProjectApproval(projectId: string): GalleryApproval {
  const approvalsData = approvals.approvals as Record<string, GalleryApproval>
  return approvalsData[projectId] || { approved: false }
}

/**
 * Get only approved projects for public display
 */
export function getApprovedProjects(): GalleryProject[] {
  return allGalleryProjects.filter(project => {
    const approval = getProjectApproval(project.id)
    return approval.approved === true
  })
}

/**
 * Legacy export for backward compatibility
 * @deprecated Use getApprovedProjects() instead
 */
export const galleryProjects = getApprovedProjects()

/* Example project entry (DO NOT add until homeowner approval is confirmed):
{
  id: "op-001",
  city: "Overland Park",
  jobType: "full-replacement",
  beforeImage: "/gallery/op-001/before.webp",
  afterImage: "/gallery/op-001/after.webp",
  beforeAlt: "Overland Park home with damaged asphalt shingles before roof replacement",
  afterAlt: "Same Overland Park home after full roof replacement with GAF Timberline HD shingles",
  description: "Full roof replacement after hail damage - GAF Timberline HD shingles",
  date: "2024-09",
  featured: true
}

Then add to gallery-approvals.json:
{
  "approvals": {
    "op-001": {
      "approved": true,
      "approvedBy": "Kevin",
      "approvedDate": "2024-11-08",
      "blurChecked": true
    }
  }
}
*/
