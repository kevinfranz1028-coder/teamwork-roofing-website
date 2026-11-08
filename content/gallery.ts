import approvals from './gallery-approvals.json'

export interface GalleryProject {
  id: string // Unique identifier (e.g., "op-001", "leawood-002")
  city: 'Overland Park' | 'Leawood' | 'Lenexa' | 'Kansas City' | 'Olathe' | 'Other'
  jobType: 'full-replacement' | 'storm-hail' | 'repair' | 'gutter' | 'siding'
  beforeImage: string // Path to before photo (e.g., "/gallery/op-001/before.webp")
  afterImage: string // Path to after photo (e.g., "/gallery/op-001/after.webp")
  beforeAlt: string // Descriptive alt text for before image
  afterAlt: string // Descriptive alt text for after image
  description: string // Short description (e.g., "Full roof replacement after hail damage - GAF Timberline HD shingles")
  date: string // Completion date in YYYY-MM format (for sorting, not displayed)
  featured: boolean // Display on homepage?
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
  // Placeholder projects (approved: false) - will be replaced with real photos once homeowner approval is confirmed
  // DO NOT add real customer photos until approval is documented in gallery-approvals.json
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
