# Gallery Photo Approval & Publishing Workflow

This document describes the process for adding homeowner-approved project photos to the Teamwork Roofing website gallery.

## Overview

The gallery system is **privacy-first by default**. All project photos require explicit homeowner approval before being published to the website. The approval tracking is separate from the code (in `content/gallery-approvals.json`), making it easy to manage without touching TypeScript files.

## Privacy Requirements

Before publishing any customer project photos:

1. **Homeowner Approval**: Written/email/text confirmation from the homeowner that they approve publication of their project photos
2. **Privacy Check**: House numbers, license plates, and faces must be blurred
3. **Location Privacy**: Photos labeled by CITY ONLY (never street address, customer name, or property details)
4. **Metadata Stripped**: ALL EXIF/GPS data removed from image files

## Photo Approval Workflow

### Step 1: Obtain Homeowner Approval

Get written confirmation (email, text, or signed form) from the homeowner that:
- They approve publication of before/after photos of their property
- They understand photos will be published on the website
- They are okay with city-level location disclosure (e.g., "Overland Park")

Save this approval documentation for records.

### Step 2: Prepare Photos Locally

Create a local folder (NOT in the repo yet) with the project photos:

```
~/teamwork-photos/op-001/
  before-raw.jpg
  after-raw.jpg
```

**Privacy checklist before processing:**
- [ ] Blur house numbers (mailbox, front door, garage)
- [ ] Blur license plates (vehicles in photo)
- [ ] Blur faces (people visible in photo)
- [ ] Verify no sensitive details visible (documents, mail, etc.)

Use Preview (Mac), Photos, Photoshop, or GIMP to blur.

### Step 3: Process Images

Once privacy checks are complete, process images with the EXIF stripping script:

```bash
# From project root
node scripts/process-gallery-images.js op-001 ~/teamwork-photos/op-001
```

This script will:
- Strip ALL EXIF/GPS metadata
- Auto-rotate images correctly
- Resize to 1200x900 (large) and 400x300 (thumbnail)
- Convert to WebP + JPEG fallback
- Output processed images to `public/gallery/<project-id>/`

Output structure:
```
public/gallery/op-001/
  before-large.webp
  before-large.jpg
  before-thumb.webp
  before-thumb.jpg
  after-large.webp
  after-large.jpg
  after-thumb.webp
  after-thumb.jpg
```

### Step 4: Add Project to Gallery Data

Edit `content/gallery.ts` and add the new project to the `allGalleryProjects` array:

```typescript
{
  id: "op-001",
  city: "Overland Park",
  jobType: "full-replacement",
  beforeImage: "/gallery/op-001/before-large.webp",
  afterImage: "/gallery/op-001/after-large.webp",
  beforeAlt: "Overland Park home with damaged asphalt shingles before roof replacement",
  afterAlt: "Same Overland Park home after full roof replacement with GAF Timberline HD shingles",
  description: "Full roof replacement after hail damage - GAF Timberline HD shingles",
  date: "2024-09", // YYYY-MM format for sorting
  featured: true // Show on homepage when approved
}
```

**City values** (must match exactly):
- `"Overland Park"`
- `"Leawood"`
- `"Lenexa"`
- `"Kansas City"`
- `"Olathe"`
- `"Other"`

**Job type values** (must match exactly):
- `"full-replacement"`
- `"storm-hail"`
- `"repair"`
- `"gutter"`
- `"siding"`

**Alt text rules:**
- City name only (no street address)
- Describe what's visible, not who owns it
- Generic descriptions (e.g., "Overland Park home" not "Smith residence")

### Step 5: Mark as Approved

Edit `content/gallery-approvals.json` and add the approval record:

```json
{
  "$schema": "./gallery-approvals.schema.json",
  "approvals": {
    "op-001": {
      "approved": true,
      "approvedBy": "Kevin",
      "approvedDate": "2024-11-08",
      "blurChecked": true
    }
  }
}
```

**Fields:**
- `approved`: `true` = photo will be visible on site, `false` = hidden
- `approvedBy`: Who confirmed approval (e.g., "Kevin", "Megan")
- `approvedDate`: Date approval was obtained (YYYY-MM-DD)
- `blurChecked`: `true` = privacy blur check completed

### Step 6: Verify EXIF Stripped

Run the EXIF check script to verify NO metadata remains:

```bash
npm run check:gallery
```

**This script MUST pass** (exit code 0) before proceeding.

If it fails:
- It will list which files contain EXIF/GPS data
- It will show GPS coordinates if found (privacy violation!)
- Re-process those images with the stripping script
- Run check again until it passes

### Step 7: Build and Test Locally

Run the Next.js build to verify everything compiles:

```bash
npm run build
```

Verify:
- Build completes successfully
- No TypeScript errors
- New project appears in build output

Start dev server to preview:

```bash
npm run dev
```

Visit:
- http://localhost:3000/gallery - verify project appears and filters work
- http://localhost:3000 - verify "Recent Work" strip shows (if featured: true AND approved: true)

### Step 8: Commit and Push

Stage the new files:

```bash
git add public/gallery/op-001/
git add content/gallery.ts
git add content/gallery-approvals.json
git status
```

Commit with descriptive message (NO customer names or addresses):

```bash
git commit -m "Add gallery project: Overland Park full replacement

- Add before/after photos for op-001 project
- GAF Timberline HD shingles, hail damage replacement
- Homeowner approval confirmed 2024-11-08
- EXIF/GPS metadata stripped and verified
- Privacy blur check completed"
```

Push to feature branch:

```bash
git push origin <branch-name>
```

### Step 9: Open Pull Request

Create PR with:
- Summary of project(s) added
- Confirmation of homeowner approval
- Confirmation `npm run check:gallery` passed
- Screenshots of gallery page with new projects

**DO NOT** include customer names, street addresses, or sensitive details in the PR description.

## File Structure

```
teamwork-roofing-website/
├── content/
│   ├── gallery.ts                      # Project data (TypeScript)
│   ├── gallery-approvals.json          # Approval tracking (separate from code)
│   └── gallery-approvals.schema.json   # JSON Schema for validation
├── public/
│   └── gallery/
│       ├── op-001/                     # Overland Park project 1
│       │   ├── before-large.webp
│       │   ├── before-large.jpg
│       │   ├── before-thumb.webp
│       │   ├── before-thumb.jpg
│       │   ├── after-large.webp
│       │   ├── after-large.jpg
│       │   ├── after-thumb.webp
│       │   └── after-thumb.jpg
│       ├── leawood-001/                # Leawood project 1
│       └── placeholder/                # Placeholder for unapproved projects
│           └── placeholder.svg
├── scripts/
│   ├── process-gallery-images.js       # Strip EXIF, optimize images
│   └── check-gallery-exif.js           # Verify no EXIF/GPS remains (npm run check:gallery)
└── docs/
    └── GALLERY.md                       # This file
```

## Project ID Naming

Use descriptive, location-based IDs:

- `op-001`, `op-002` - Overland Park projects
- `leawood-001`, `leawood-002` - Leawood projects
- `lenexa-001` - Lenexa projects
- `kc-001` - Kansas City projects
- `olathe-001` - Olathe projects

IDs must be:
- Unique across all projects
- Lowercase with hyphens
- No customer names or addresses

## Troubleshooting

### "EXIF/GPS data found" error

If `npm run check:gallery` fails:

1. Check which files are flagged in the error output
2. Re-run the processing script on those files
3. Verify the processed images were moved to `public/gallery/`
4. Run check again

**NEVER commit images with EXIF/GPS data.** This is a privacy violation.

### Project not appearing on site

Check:
1. `content/gallery-approvals.json` has `"approved": true` for that project ID
2. Project ID in `gallery.ts` matches exactly with approvals.json
3. `npm run build` completed successfully
4. Dev server was restarted after changes

### TypeScript errors

If you get type errors in `gallery.ts`:
- Verify city name matches the union type exactly (case-sensitive)
- Verify jobType matches one of the allowed values
- Verify all required fields are present
- Run `npm run build` to see the exact error

### "Recent Work" strip not showing on homepage

The strip only shows when:
- At least 1 project has `approved: true` in gallery-approvals.json
- That project is in the `allGalleryProjects` array in gallery.ts

Currently the strip is **hidden** because there are no approved projects yet.

## Privacy Violations - DO NOT:

❌ Include customer names in filenames, alt text, descriptions, or commit messages  
❌ Include street addresses anywhere  
❌ Publish photos without homeowner approval  
❌ Publish photos with visible EXIF/GPS data  
❌ Publish photos with unblurred house numbers, plates, or faces  
❌ Use customer-identifying information in project IDs  

## Approval Tracking

The `content/gallery-approvals.json` file is the source of truth for which projects can be published. This separation allows:

1. **Easy management**: Toggle approved status without editing TypeScript
2. **Audit trail**: Track who approved and when
3. **Safety**: Default to hidden (unapproved projects don't appear)
4. **Flexibility**: Can revoke approval by setting `"approved": false`

The TypeScript file (`gallery.ts`) defines the projects and their data.  
The JSON file (`gallery-approvals.json`) controls which ones are visible.

## Homepage Display

Projects marked `featured: true` in `gallery.ts` AND `approved: true` in `gallery-approvals.json` will appear in the homepage "Recent Work" strip (up to 3 most recent by date).

The "Recent Work" strip only renders when at least 1 approved project exists. Currently it is **hidden** (no approved projects yet).

## Inspection-Only Projects (afterPending Flag)

Some projects document damage inspections where repair/replacement photos will be added later. These use the `afterPending: true` flag.

### When to Use afterPending

Use `afterPending: true` for:
- Hail/storm damage inspections (before work is scheduled)
- Projects awaiting insurance approval
- Jobs where "after" photos will be available later

### How afterPending Works

When `afterPending: true`:
1. **No "Before" badge** is shown (avoids implying work is complete)
2. **The "After" image slot stays hidden** (even if afterImage is undefined)
3. **Featured display images** show first (e.g., olathe-002 shows before-1, before-2, before-3, detail-3, detail-5)
4. **Remaining additionalImages** go in a lightbox accessible via "View More Photos" button
5. **Gallery page renders as inspection layout** instead of before/after columns

### Example: olathe-002

```typescript
{
  id: "olathe-002",
  city: "Olathe",
  jobType: "inspection",
  beforeImage: "/gallery/olathe-002/olathe-002-before-1.jpg",
  // NO afterImage field (undefined)
  beforeAlt: "Hail damage inspection - Olathe, Kansas",
  // NO afterAlt (undefined)
  description: "Hail damage inspection",
  date: "2026-11",
  featured: true,
  afterPending: true, // <-- Key flag
  additionalImages: [
    "/gallery/olathe-002/olathe-002-before-1.jpg",
    "/gallery/olathe-002/olathe-002-before-2.jpg",
    // ... 18 total photos
  ]
}
```

### Converting to Full Before/After (Adding After Photos)

When the project is complete and you have after photos:

1. **Add after photos** to the project folder:
   ```bash
   public/gallery/olathe-002/
     olathe-002-after-1.jpg
     olathe-002-after-2.jpg
   ```

2. **Update gallery.ts**:
   ```typescript
   {
     id: "olathe-002",
     city: "Olathe",
     jobType: "full-replacement", // Changed from "inspection"
     beforeImage: "/gallery/olathe-002/olathe-002-before-1.jpg",
     afterImage: "/gallery/olathe-002/olathe-002-after-1.jpg", // ✅ Added
     beforeAlt: "Olathe home with hail damage before roof replacement",
     afterAlt: "Same Olathe home after full roof replacement", // ✅ Added
     description: "Full roof replacement after hail damage",
     date: "2026-11",
     featured: true,
     afterPending: false, // ✅ Changed to false (or remove field entirely)
     additionalImages: [ /* keep existing detail shots */ ]
   }
   ```

3. **Update HomeHero** (if this becomes the homepage hero):
   - Edit `components/HomeHero.tsx`
   - Change `kansas-city-ks-001` references to `olathe-002`
   - Update captions to match the project
   - Update alt text to describe the Olathe project

4. **Verify and commit**:
   ```bash
   npm run check:gallery  # Verify EXIF stripped
   npm run build          # Verify build passes
   git add public/gallery/olathe-002/ content/gallery.ts components/HomeHero.tsx
   git commit -m "Complete olathe-002: add after photos"
   ```

### Featured Hero Swap

To make olathe-002 the homepage hero once after photos are added:

1. Complete the steps above (add after photos, set afterPending: false)
2. Edit `components/HomeHero.tsx`:
   ```tsx
   // Replace kansas-city-ks-001 with olathe-002
   <Image
     src="/gallery/olathe-002/olathe-002-before-1.jpg"
     alt="Olathe home with hail damage before roof replacement"
     // ... rest of props
   />
   ```
3. Update captions:
   - Before: "Before roof replacement" or custom caption
   - After: "Completed roof" or custom caption
4. Test locally, commit, and push

This makes olathe-002 the featured hero while keeping kansas-city-ks-001 in the gallery.

## Questions

Contact Kevin or Megan for:
- Homeowner approval confirmation
- Privacy blur requirements
- Which projects to prioritize for gallery
- Photo quality review before publishing
