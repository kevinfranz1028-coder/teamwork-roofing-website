# Gallery Photo Guidelines & Upload Process

This document explains how to add before/after project photos to the gallery.

## Photo Requirements

### Legal & Privacy

**REQUIRED BEFORE UPLOADING:**
- [ ] Homeowner permission obtained (written or documented verbal OK)
- [ ] No visible house numbers
- [ ] No visible license plates
- [ ] No identifiable people in frame
- [ ] GPS/EXIF data will be stripped (script handles this)

**Location Privacy:**
- Gallery labels show **CITY ONLY** (e.g., "Overland Park")
- NEVER include street address, neighborhood name, or identifying landmarks
- Alt text describes work, NOT location specifics

### Photo Quality

**Technical Requirements:**
- Minimum resolution: 1920x1080px
- Format: JPEG, PNG, or HEIC (script converts to WebP + JPEG)
- File size: Any (script optimizes)
- Orientation: Any (script auto-rotates)

**Composition Guidelines:**
- **Same angle:** Before and after should be shot from similar position
- **Show whole roof** when possible (or full project area for siding/gutters)
- **Good lighting:** Avoid deep shadows or overexposure
- **Clear sky preferred:** Clouds OK, but consistent between before/after is best

### File Naming

Input files must contain "before" or "after" in filename:
- ✅ `overland-park-before.jpg`
- ✅ `BEFORE_20241015.HEIC`
- ✅ `project_after.png`
- ❌ `IMG_1234.jpg` (no before/after indicator)

## Upload Process

### Step 1: Organize Source Photos

Create a folder for each project with before/after pair:

```
~/Desktop/gallery-photos/
├── overland-park-001/
│   ├── before.jpg
│   └── after.jpg
├── leawood-002/
│   ├── before.heic
│   └── after.heic
└── lenexa-003/
    ├── BEFORE_20241015.jpg
    └── AFTER_20241015.jpg
```

### Step 2: Verify Photo Privacy

For each photo:
- [ ] Blur any house numbers (use Preview, Photos, or Photoshop)
- [ ] Blur any license plates
- [ ] Blur any faces if people visible
- [ ] Confirm homeowner permission documented

### Step 3: Run Processing Script

```bash
# Install sharp (first time only)
npm install sharp

# Process one project
node scripts/process-gallery-images.js <project-id> <input-folder>

# Example:
node scripts/process-gallery-images.js op-001 ~/Desktop/gallery-photos/overland-park-001
```

The script will:
1. Strip ALL EXIF/GPS metadata
2. Auto-rotate images
3. Resize to 1200x900 (large) and 400x300 (thumbnail)
4. Output as WebP + JPEG fallback
5. Save to `public/gallery/<project-id>/`

Output files:
```
public/gallery/op-001/
├── before-large.webp
├── before-large.jpg
├── before-thumb.webp
├── before-thumb.jpg
├── after-large.webp
├── after-large.jpg
├── after-thumb.webp
└── after-thumb.jpg
```

### Step 4: Add to Gallery Data

Edit `content/gallery.ts` and add the project:

```typescript
{
  id: "op-001",
  city: "Overland Park", // City only - NO street address
  jobType: "full-replacement", // or "storm-hail", "repair", "gutter", "siding"
  beforeImage: "/gallery/op-001/before-large.webp",
  afterImage: "/gallery/op-001/after-large.webp",
  beforeAlt: "Overland Park home with damaged asphalt shingles before roof replacement",
  afterAlt: "Same Overland Park home after full roof replacement with GAF Timberline HD shingles",
  description: "Full roof replacement after hail damage - GAF Timberline HD shingles",
  date: "2024-11", // Month project completed (YYYY-MM)
  featured: false // Set true for homepage display (max 3 featured)
}
```

**Alt Text Guidelines:**
- Describe the work, materials, condition
- Include city name (for SEO)
- Be specific but concise
- Example: "Leawood home with missing shingles before storm damage repair"
- NOT: "Before photo" or "Roof before"

### Step 5: Test

```bash
# Build and check
npm run build

# Start dev server
npm run dev
```

Visit http://localhost:3000/gallery/ and verify:
- Images load correctly
- Alt text appears on hover
- Filters work (city and job type)
- No personal information visible

### Step 6: Commit

```bash
git add public/gallery/<project-id>/ content/gallery.ts
git commit -m "Add gallery project: <project-id>"
```

## Project ID Naming Convention

Format: `<city-code>-<number>`

**City Codes:**
- `op` = Overland Park
- `leawood` = Leawood
- `lenexa` = Lenexa
- `kc` = Kansas City (MO or KS)
- `other` = Other KC Metro cities

**Examples:**
- `op-001`, `op-002`, `op-003` (Overland Park projects)
- `leawood-001`, `leawood-002` (Leawood projects)
- `kc-001` (Kansas City project)

**Numbering:**
- Sequential within each city
- Zero-padded to 3 digits (001, 002, ... 999)
- Check `content/gallery.ts` for highest number in each city

## Featured Projects

The homepage displays up to 3 featured projects (set `featured: true`).

**Selection Criteria:**
- Best photo quality
- Dramatic before/after transformation
- Recent work (within last 6 months)
- Diverse job types (mix of full replacement, storm damage, etc.)
- Geographic spread (not all from one city)

## Troubleshooting

### "Could not find before/after images"
- Filenames must contain "before" or "after" (case-insensitive)
- Check folder path is correct
- Verify files are image formats (jpg, png, heic)

### "Error: Input folder not found"
- Use absolute path or path relative to repo root
- Check for typos in folder path
- Ensure folder exists

### Images look rotated wrong
- Script auto-rotates based on EXIF
- If still wrong, manually rotate before processing
- Some phone cameras don't set EXIF correctly

### File size too large
- Script optimizes automatically
- WebP output is typically 30-50% smaller than JPEG
- If still concerned, reduce source image resolution before processing

## Privacy Checklist (Before Publishing)

For EACH photo:
- [ ] Homeowner permission documented
- [ ] House numbers blurred or not visible
- [ ] License plates blurred or not visible  
- [ ] No people visible (or faces blurred)
- [ ] City-only label (NO street address)
- [ ] Alt text describes work, not location specifics
- [ ] GPS/EXIF stripped (script does this automatically)

## Questions?

Contact Kevin for:
- Homeowner permission confirmation
- Project details (materials, job type, date)
- Photo approval before publishing
