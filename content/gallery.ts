export interface GalleryProject {
  id: string // Unique identifier (e.g., "op-001", "leawood-002")
  city: 'Overland Park' | 'Leawood' | 'Lenexa' | 'Kansas City' | 'Other'
  jobType: 'full-replacement' | 'storm-hail' | 'repair' | 'gutter' | 'siding'
  beforeImage: string // Path to before photo (e.g., "/gallery/op-001/before.webp")
  afterImage: string // Path to after photo (e.g., "/gallery/op-001/after.webp")
  beforeAlt: string // Descriptive alt text for before image
  afterAlt: string // Descriptive alt text for after image
  description: string // Short description (e.g., "Full roof replacement after hail damage - GAF Timberline HD shingles")
  date: string // Completion date in YYYY-MM format (for sorting, not displayed)
  featured: boolean // Display on homepage?
}

// Gallery projects - EMPTY until Kevin provides photos
// See docs/GALLERY.md for photo requirements and upload process
export const galleryProjects: GalleryProject[] = []

/* Example project structure (DO NOT UNCOMMENT until real photos are added):
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
*/
