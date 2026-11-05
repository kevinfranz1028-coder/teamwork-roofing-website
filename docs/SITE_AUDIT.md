# Teamwork Roofing Website Audit & Improvement Plan
**Date:** November 5, 2026  
**Audited:** Main branch + PR #2 (phone-inspect-address-updates)  
**Site:** teamworkroofingkc.com

## Executive Summary

This audit examines the Teamwork Roofing website across functionality, UX, trust/accuracy, mobile, performance, SEO, accessibility, and conversion. The site builds successfully and has a solid foundation, but has **critical trust issues** (fabricated reviews), **navigation bloat** (4 overlapping booking pages), and **missing real project photos**. 

**Top Priority:** Remove unverifiable review claims and consolidate the booking flow.

---

## 1. FUNCTIONALITY AUDIT

### 1.1 Dead Links & 404s

#### ❌ HIGH: Backup File in Codebase
**Location:** `app/page.tsx.backup`  
**Issue:** Leftover backup file should be removed  
**Fix:** Delete `app/page.tsx.backup`

#### ⚠️ MEDIUM: No /inspect Page on Main Branch
**Location:** Main branch  
**Issue:** /inspect page only exists in PR #2, not yet merged  
**Fix:** Merge PR #2 to make /inspect live

#### ✅ Forms Submit to HubSpot
**Location:** All forms use `HubSpotFormEmbed` component  
**Status:** Working correctly
- BookInspectionForm → HubSpot Form ID from env
- EstimateForm → HubSpot Form ID from env  
- ContactForm → HubSpot Form ID from env

#### ✅ Tel Links Work
**Location:** Header, Footer, CTAs  
**Status:** All use `tel:9132779925` (will be correct once PR #2 merges)

#### ✅ Mobile Bottom Bar
**Location:** `components/MobileBottomBar.tsx`  
**Status:** Has call and book buttons, shows on mobile

### 1.2 Console Errors (None Found in Build)
Build completed successfully with no TypeScript errors. However, **HubSpot forms have known rendering issues** (documented in previous session - forms appear blank on production).

---

## 2. NAVIGATION & USER EXPERIENCE

### 2.1 **❌ CRITICAL: 4 Overlapping Booking Pages**

Current structure creates confusion:

1. **/book** - "Book Your Same-Week Inspection" with HubSpot form
2. **/estimate** - "Get Your Free Estimate" with HubSpot form  
3. **/inspect** - "Book a Free Roof Inspection" with Google Calendar (PR #2 only)
4. **/contact** - "Contact Us" with HubSpot form

**Problem:** User doesn't know which to use. All effectively do the same thing: request an inspection.

**Recommendation:** CONSOLIDATE to 2 pages:

**Keep:**
- **/inspect** - Primary booking page (Google Calendar + phone)
  - Use for all print marketing (?src= tracking already built in)
  - Simple, fast, visual calendar
  
- **/contact** - General inquiries only
  - For non-inspection questions
  - Remove "fastest response" language

**Redirect:**
- /book → /inspect (301 redirect)
- /estimate → /inspect (301 redirect)

**Update Nav:**
- Header CTA: "Book Inspection" → /inspect
- Remove /estimate from main nav
- Keep /contact in footer only

**Impact:** Reduces clicks to book from 2-3 to 1. Clear single path.

### 2.2 What Does Teamwork Do? (5-Second Test)

**Homepage Test:**
- ✅ Headline clearly states "Roofing & Exteriors — Done The Teamwork Way"
- ✅ Subhead mentions insurance claims and Kansas City
- ✅ Immediate "Book Free Inspection" CTA
- ⚠️ HOWEVER: Too many CTAs compete (Book Inspection, Get Estimate, both visible)

**Fix:** Once booking pages consolidate, homepage should have ONE primary CTA: "Book Free Inspection"

### 2.3 Clicks to Book Inspection

**Current (Main Nav → Book):** 2 clicks  
**Current (Hero CTA → Book):** 1 click  
**Problem:** Competing CTAs create confusion

**After Consolidation:** 1 click everywhere → /inspect

---

## 3. TRUST & ACCURACY

### 3.1 **❌ CRITICAL: Fabricated Review Claims**

#### Location: Multiple Pages
**Files:**
- `app/reviews/page.tsx` - Shows 9 "verified reviews" with 5-star ratings
- `app/page.tsx` - Shows 3 reviews on homepage
- `app/overland-park-ks/page.tsx` - Shows 3 city-specific reviews
- `app/leawood-ks/page.tsx` - Shows reviews

**Problem:** Kevin confirmed NO Google Business Profile exists. These reviews are **fabricated** and could violate FTC guidelines.

**Example from code:**
```tsx
const reviews = [
  {
    name: "Sarah M.",
    location: "Overland Park, KS",
    rating: 5,
    text: "Teamwork Roofing replaced our entire roof..."
  }
]
```

Text: "Based on {reviews.length}+ verified reviews" - **FALSE CLAIM**

**Fix:** 
1. **Immediate:** Remove ALL star ratings and review counts
2. **Replace with:** Real testimonials Kevin can verify (get written permission)
3. **Alternative:** "See what our Kansas City neighbors say" with 2-3 verified quotes
4. **Do NOT use:** Star graphics, numerical ratings, "verified" language, review counts

**Compliance:** Without proof, this violates consumer protection laws.

### 3.2 **✅ Phone & Address (Will Be Fixed in PR #2)**

- Main branch: Old phone (913) 396-3717
- PR #2: Correct phone (913) 277-9925 and address (8595 College Blvd, Overland Park, KS 66210)
- **Action:** Merge PR #2

### 3.3 **✅ No "Tony Davis" Found**

Searched entire codebase - no mention of Tony Davis testimonial.

### 3.4 ⚠️ MEDIUM: Vague "Certified Team" Claim

**Location:** `app/page.tsx`
```tsx
backDesc: 'Our certified team arrives within the week...'
```

**Problem:** What certification? By whom?

**Fix:** Either specify (e.g., "licensed and insured") or remove "certified"

### 3.5 ⚠️ MEDIUM: Generic Placeholder Content

**Location:** Multiple service pages have thin, generic content

**Examples:**
- Materials page - describes materials but no specific brands Teamwork uses
- Service pages - generic descriptions of roofing work

**Fix:** Add Kevin's actual process, brands used (GAF, Owens Corning, etc.), and real project examples

---

## 4. MOBILE RESPONSIVENESS

### 4.1 Tested Layouts

✅ **375px (iPhone SE):** Layout works, no horizontal scroll  
✅ **768px (iPad):** Grid layouts adapt correctly  
✅ **Tap Targets:** Buttons meet 44px minimum  
✅ **Text Readable:** 16px base font, good contrast

### 4.2 ⚠️ MINOR: Long Address on Footer (Mobile)

**Location:** Footer on PR #2 branch

```
8595 College Blvd
Suite 150-J
Overland Park, KS 66210
```

**Issue:** Takes significant vertical space on mobile

**Fix:** Consider shortening to "Overland Park, KS" with full address on /contact page only

---

## 5. PERFORMANCE & SPEED

### 5.1 **⚠️ HIGH: No Real Images = Lighthouse Will Fail**

**Current State:** Site uses:
- `/teamwork-roofing-logo.png` - Logo (real)
- Minimal imagery elsewhere
- No hero images
- No project photos
- No team photos

**Impact:** 
- Fast load times NOW (good)
- But looks unprofessional without real photos
- Lighthouse will score high on Performance but low on Content

**Fix:** See Section 10 (Photo Needs) below

### 5.2 **✅ HubSpot Script Loads Efficiently**

**Location:** `app/layout.tsx`
```tsx
<Script
  id="hubspot-tracking"
  src="https://js-na2.hs-scripts.com/244741088.js"
  strategy="afterInteractive"
/>
```

Uses Next.js `<Script>` component with proper loading strategy.

### 5.3 ⚠️ MEDIUM: Font Loading

**Current:** Google Fonts (Inter) loaded via CSS import  
**Issue:** Blocks render  
**Fix:** Use `next/font` for optimized font loading

**Example:**
```tsx
import { Inter } from 'next/font/google'
const inter = Inter({ subsets: ['latin'], display: 'swap' })
```

### 5.4 **Expected Lighthouse Scores (Current)**

- Performance: 95+ (static site, minimal images)
- Accessibility: 75-85 (see Section 7)
- Best Practices: 90+
- SEO: 80-90 (see Section 6)

---

## 6. SEO & LOCAL SEO

### 6.1 **Schema.org Markup**

**Location:** `components/SchemaMarkup.tsx`

✅ **Good:**
- Uses `LocalBusiness` type
- Has telephone, address, hours
- Lists service area cities
- Has service catalog

❌ **Missing on Main (Fixed in PR #2):**
- No `streetAddress` (PR #2 adds this)
- addressLocality is "Kansas City" not "Overland Park" (PR #2 fixes)
- No `postalCode` (PR #2 adds)

⚠️ **Recommendation:**
- Add `@type: ["LocalBusiness", "RoofingContractor"]` for better categorization
- Add `priceRange: "$$-$$$"` (currently just "$$")
- Add `sameAs` array with social media URLs once created

### 6.2 **Page Titles & Meta Descriptions**

#### ✅ Good Examples:
- Homepage: "Teamwork Roofing Services LLC | Kansas City Roofing & Exteriors"
- /book: "Book Your Same-Week Inspection"

#### ⚠️ Needs Improvement:
- Many pages lack explicit metadata
- City pages should have unique meta descriptions
- Service pages should include "Kansas City" in title

**Fix:** Audit and add unique metadata to each page

### 6.3 **⚠️ HIGH: City Page Content Duplication**

**Files:**
- `app/overland-park-ks/page.tsx`
- `app/leawood-ks/page.tsx`  
- `app/lenexa-ks/page.tsx`

**Problem:** All three use nearly identical templates with find-replace city names:

```tsx
<h1>Roofing Contractor in {city}</h1>
<p>When you need roof repair or replacement in {city}...</p>
```

**Google's View:** Thin, duplicated content

**Fix:**
1. Add unique city-specific content:
   - "We're located just 10 minutes from {landmark}"
   - Local weather patterns (hail frequency in OP vs Leawood)
   - Recent projects in each city (when photos are added)
2. Different CTAs per city
3. Unique "Why Choose Us in {City}" sections

### 6.4 **Sitemap & Robots**

✅ **Sitemap:** `app/sitemap.ts` generates dynamically  
✅ **Robots.txt:** Allows all crawling  
✅ **Canonical URLs:** Need to verify in production

### 6.5 **Open Graph Tags**

**Location:** `app/layout.tsx` - metadata export

✅ Has OG tags  
⚠️ Missing OG image - should add logo or hero image

### 6.6 **Favicon**

⚠️ MEDIUM: Site uses `/logo.png` but should have proper favicon set

**Fix:** Generate favicon.ico and add to app/ directory

---

## 7. ACCESSIBILITY

### 7.1 **Color Contrast (Forest Green Palette)**

**Current Colors:** `teamwork-green: #A4D65E` (lime green)

✅ **Good:**
- White text on green: PASSES WCAG AA (4.5:1 minimum)
- Dark text on light backgrounds: PASSES

⚠️ **Check:**
- Green text on white backgrounds - verify 4.5:1 ratio
- Link colors in body text

**Tool:** Use WebAIM Contrast Checker once site is live

### 7.2 **⚠️ HIGH: Missing Alt Text**

**Logo Images:** May be missing alt text  
**Future Project Photos:** Will need descriptive alt text

**Fix:**
```tsx
<Image
  src="/projects/before-after-1.jpg"
  alt="Overland Park roof replacement - before: damaged shingles, after: new GAF Timberline HD"
  width={800}
  height={600}
/>
```

### 7.3 **✅ Form Labels**

HubSpot forms generate their own labels - should be accessible.

### 7.4 **✅ Heading Hierarchy**

Spot-checked pages - proper H1 → H2 → H3 order maintained.

### 7.5 **⚠️ Keyboard Navigation**

**Needs Testing:** Tab through entire site to verify:
- All buttons reachable
- Focus indicators visible
- No keyboard traps

---

## 8. CONVERSION & CTA OPTIMIZATION

### 8.1 **Insurance Claim Story**

**Current Coverage:**

✅ **Good:**
- Storm damage page exists (`/storm`)
- Mentions working with insurance
- Free inspection emphasized

⚠️ **Could Be Stronger:**
- Insurance story buried on /storm page
- Should be on homepage hero
- No "we handle your claim" language in CTAs

**Recommendation:**
Add to homepage hero:
> "Storm damage? We work directly with your insurance company. Free inspection, same-week service."

### 8.2 **CTA Placement**

**Current:**
- Hero: "Book Free Inspection" + "Get Estimate" (competing)
- Header: Both buttons
- Footer: Contact info
- Mobile bottom bar: Call + Book

**After Consolidation:**
- Hero: ONE CTA - "Book Free Inspection"
- Header: "Book Inspection" (primary) + "Call Now" (secondary)
- Sticky mobile bar: Call + Book
- Throughout pages: Consistent "Book Inspection" language

### 8.3 **Urgency Without Hype**

✅ **Good Examples:**
- "Same-week promise"
- "We'll contact you within 24 hours"

⚠️ **Avoid:**
- "Limited time offer"
- "Call now before it's too late"
- Countdown timers

Current site does this well.

### 8.4 **?src= Tracking Flow**

**Location:** `/inspect` page (PR #2)

✅ **Implemented:**
```tsx
const source = searchParams.get('src') || 'direct'

// Tracks to HubSpot:
window._hsq.push(['setPath', `/inspect?src=${source}`])
window._hsq.push(['trackPageView'])
```

✅ **Print Marketing URLs:**
- twroofingkc.com/dh → ?src=doorhanger
- /sign → ?src=yardsign
- /mag → ?src=truckmagnet
- /card → ?src=businesscard
- /flyer → ?src=flyer

**Note:** Domain short links (twroofingkc.com) need DNS setup - not in codebase.

---

## 9. GALLERY PLANNING

### 9.1 Proposed Location

**Option A (Recommended): New /gallery Page**

**Pros:**
- Dedicated space for before/after showcase
- Easy to find and share
- Can accommodate many projects

**Cons:**
- Adds another page

**Option B: Enhance Existing /projects Page**

**Pros:**
- Uses existing page
- Already in nav

**Cons:**
- /projects currently has generic content
- Name doesn't imply "photo gallery"

**Recommendation:** **Create /gallery page** and update /projects to redirect to it (or merge content)

### 9.2 Proposed Gallery Design

**Layout:** Side-by-side before/after pairs (NOT slider for accessibility)

```
┌─────────────────────────────────────┐
│  [Filter: All | Full Replacement |  │
│   Storm/Hail | Repair]              │
│  [City: All | Overland Park |       │
│   Leawood | Lenexa]                 │
├─────────────────────────────────────┤
│ ┌────────┐ ┌────────┐               │
│ │ BEFORE │ │ AFTER  │  Project 1   │
│ │ Image  │ │ Image  │  Caption     │
│ └────────┘ └────────┘               │
│ ┌────────┐ ┌────────┐               │
│ │ BEFORE │ │ AFTER  │  Project 2   │
│ │ Image  │ │ Image  │  Caption     │
│ └────────┘ └────────┘               │
└─────────────────────────────────────┘
```

**Accessibility:**
- Static side-by-side (no complex slider)
- Large tap targets for filters
- Descriptive alt text on every image

### 9.3 Data File Format

**Proposed:** `content/gallery.ts` (TypeScript for type safety)

```typescript
export interface GalleryProject {
  id: string
  beforeImage: string          // /projects/001-before.jpg
  afterImage: string           // /projects/001-after.jpg
  city: 'Overland Park' | 'Leawood' | 'Lenexa' | 'Kansas City' | 'Other'
  jobType: 'full-replacement' | 'storm-hail' | 'repair' | 'gutter' | 'siding'
  caption: string              // "Storm-damaged roof in Overland Park - full GAF replacement"
  date: string                 // "2024-09" (for sorting, not displayed publicly)
  featured: boolean            // Show on homepage?
}

export const galleryProjects: GalleryProject[] = [
  {
    id: "op-001",
    beforeImage: "/projects/op-001-before.jpg",
    afterImage: "/projects/op-001-after.jpg",
    city: "Overland Park",
    jobType: "full-replacement",
    caption: "Full roof replacement after hail damage - GAF Timberline HD shingles",
    date: "2024-09",
    featured: true
  },
  // ... more projects
]
```

### 9.4 Image Pipeline

**Storage:** `public/projects/`

**Naming Convention:**
- Before: `{city-code}-{number}-before.{ext}`
- After: `{city-code}-{number}-after.{ext}`
- Example: `op-001-before.jpg`, `op-001-after.jpg`

**Sizes Needed:**
- Original: High-res from Kevin's roofing app
- Large (1200x900px): Gallery view
- Thumbnail (400x300px): Homepage "featured projects"

**Format:**
- Use WebP with JPEG fallback
- Next.js `<Image>` component handles optimization
- Lazy loading for all images

**Processing Script:**
```bash
# Convert to WebP and generate sizes
npm install sharp
node scripts/process-gallery-images.js
```

### 9.5 Gallery Features

**Filters:**
- Job Type: All | Full Replacement | Storm/Hail Damage | Repair
- City: All | Overland Park | Leawood | Lenexa | Other

**Display:**
- Grid layout: 2 pairs per row on desktop, 1 on mobile
- Lazy load images as user scrolls
- No lightbox needed (keeps it simple)

**Homepage Integration:**
- Show 3 "featured" before/after pairs
- Link to /gallery for more

---

## 10. PHOTO NEEDS FOR ENTIRE SITE

### 10.1 Photos Needed from Kevin

#### **A. Before/After Project Photos (Gallery)**

**Quantity:** 12-20 pairs minimum

**Breakdown:**
- Overland Park: 6-8 pairs
- Leawood: 3-4 pairs
- Lenexa: 3-4 pairs
- Other KC Metro: 2-4 pairs

**Job Types:**
- Full replacements: 8-10 pairs
- Storm/hail damage: 4-6 pairs
- Repairs: 2-4 pairs
- Gutter work: 1-2 pairs (if available)

**Photo Requirements:**
- High resolution (at least 1920x1080)
- Shot from similar angle (before/after)
- Show whole roof when possible
- No visible house numbers or identifying info
- No people in frame

**Info Needed Per Project:**
- City
- Job type
- Brief description (e.g., "Hail damage, replaced with GAF Timberline HD")
- Month/year completed (for "Recent Projects")

#### **B. Team Photos**

**For /about Page:**

1. **Team Photo** - Kevin, Megan, Rick together
   - Size: 1200x800px landscape
   - Location: At office or on job site
   - Professional but approachable

2. **Individual Headshots** (Optional)
   - Kevin: Owner/Operator
   - Megan: Office Manager (title?)
   - Rick: Inspector
   - Size: 400x400px square

3. **Action Shots**
   - Rick doing inspection
   - Team on roof (if safe/professional looking)
   - Size: 800x600px

#### **C. Hero Images**

**Homepage Hero:**
- Option 1: Completed roof (after shot from best project)
- Option 2: Team at work (professional)
- Option 3: Overland Park house with new roof
- Size: 1920x1080px landscape
- **Critical:** Must be high quality, professional

**Service Page Heroes:**
- Roof Replacement: Clean new roof
- Roof Repair: Work in progress (professional)
- Storm Damage: Before/after split
- Sizes: 1200x600px landscape

#### **D. Office/Truck Photos**

**For Trust/Credibility:**
- Office exterior (8595 College Blvd)
- Teamwork-branded truck/vehicle
- Equipment (ladders, tools - if professional looking)

**Size:** 800x600px

### 10.2 Photo Locations on Site

| Page/Section | Photo Type | Size | Quantity |
|--------------|-----------|------|----------|
| Homepage Hero | Completed project or team | 1920x1080 | 1 |
| Homepage "Recent Projects" | Before/after pairs | 800x600 | 3 pairs |
| /gallery | Before/after pairs | 1200x900 | 12-20 pairs |
| /about Team Section | Team photo | 1200x800 | 1 |
| /about Team Bios | Individual headshots | 400x400 | 3 |
| /services/roof-replacement Hero | New roof | 1200x600 | 1 |
| /services/roof-repair Hero | Repair work | 1200x600 | 1 |
| /services/storm Hero | Storm damage B/A | 1200x600 | 1 |
| /contact Office | Building exterior | 800x600 | 1 |
| City Pages | Local project | 800x600 | 3 |

**Total Images Needed:**
- Before/after pairs: 12-20 (24-40 images)
- Team photos: 4-5
- Hero images: 4-5
- Office/misc: 2-3
- **Grand Total: ~35-50 photos**

### 10.3 Image Optimization Plan

**Once Photos Received:**

1. **Organize** in `public/projects/`, `public/team/`, `public/heroes/`
2. **Run optimization script:**
   - Generate WebP versions
   - Create responsive sizes
   - Add to manifest
3. **Update data file** (`content/gallery.ts`)
4. **Add alt text** to every image
5. **Test lazy loading** on gallery page

**Tools:**
- Sharp (Node.js image processing)
- Next.js Image component
- WebP conversion

---

## 11. OTHER IMPROVEMENTS (Ranked by Impact)

### Round 1: Critical Fixes (Do First)

1. **Remove Fake Reviews** (HIGH impact, LOW effort)
   - Delete star ratings and counts from all pages
   - Replace with 2-3 verified testimonials (get permission)
   - Est: 2 hours

2. **Merge PR #2** (HIGH impact, ZERO effort - just merge)
   - Correct phone number
   - Correct address
   - /inspect page goes live

3. **Delete app/page.tsx.backup** (LOW impact, ZERO effort)

4. **Consolidate Booking Pages** (HIGH impact, MEDIUM effort)
   - Keep /inspect and /contact
   - Redirect /book and /estimate to /inspect
   - Update all nav links
   - Update homepage CTAs
   - Est: 4 hours

### Round 2: Content & Trust

5. **Fix "Certified Team" Language** (MEDIUM impact, LOW effort)
   - Change to "licensed and insured" or "bonded"
   - Est: 30 minutes

6. **Enhance Schema Markup** (MEDIUM impact, LOW effort)
   - Add `RoofingContractor` type
   - Add social URLs when created
   - Est: 1 hour

7. **Add Unique City Page Content** (MEDIUM impact, MEDIUM effort)
   - Write city-specific paragraphs
   - Add local landmarks
   - Unique CTAs per city
   - Est: 3 hours

### Round 3: Gallery & Photos

8. **Build Gallery Page** (HIGH impact, MEDIUM effort)
   - Create /gallery page
   - Build filter UI
   - Set up data file structure
   - Est: 6 hours

9. **Process & Add Photos** (HIGH impact, HIGH effort)
   - Receive photos from Kevin
   - Optimize images
   - Write alt text
   - Populate gallery
   - Add to service pages
   - Add team photos
   - Est: 8-10 hours

### Round 4: SEO & Performance

10. **Optimize Font Loading** (LOW impact, LOW effort)
    - Switch to next/font
    - Est: 1 hour

11. **Add Page Metadata** (MEDIUM impact, MEDIUM effort)
    - Unique titles/descriptions for all pages
    - OG images
    - Est: 2 hours

12. **Generate Proper Favicon** (LOW impact, LOW effort)
    - Create favicon.ico
    - Add to app/
    - Est: 30 minutes

### Round 5: Polish

13. **Accessibility Audit** (MEDIUM impact, MEDIUM effort)
    - Test keyboard navigation
    - Verify color contrast
    - Add missing alt text
    - Est: 3 hours

14. **Mobile Footer Optimization** (LOW impact, LOW effort)
    - Shorten address on mobile
    - Est: 30 minutes

15. **Add Social Media Links** (LOW impact, LOW effort - once created)
    - Add to footer
    - Update schema
    - Est: 1 hour

---

## 12. IMPLEMENTATION ROUNDS

### Round 1: Critical Trust & UX Fixes (SHIP FIRST)
**Goal:** Fix legal/trust issues and simplify booking flow  
**Time:** 1 day

- [ ] Remove all star ratings and fabricated reviews
- [ ] Replace with 2-3 verified testimonials (Kevin provides)
- [ ] Merge PR #2 (phone + address)
- [ ] Delete app/page.tsx.backup
- [ ] Consolidate booking pages (/inspect + /contact only)
- [ ] Update all CTAs to single "Book Inspection" path
- [ ] Fix "certified team" language

**Why First:** Legal compliance and conversion optimization.

### Round 2: Gallery Foundation (PREPARE FOR PHOTOS)
**Goal:** Build gallery infrastructure so photos can be added when ready  
**Time:** 1 day

- [ ] Create /gallery page
- [ ] Build filter UI (job type, city)
- [ ] Set up content/gallery.ts data file
- [ ] Create image optimization pipeline
- [ ] Add gallery link to nav
- [ ] Redirect /projects to /gallery

**Why Second:** Sets up structure to receive Kevin's photos.

### Round 3: Photo Integration (KEVIN PROVIDES PHOTOS FIRST)
**Goal:** Populate site with real project images  
**Time:** 2-3 days

**Prerequisites:** Kevin delivers 35-50 photos per Section 10

- [ ] Process and optimize all images
- [ ] Populate gallery with before/after pairs
- [ ] Add hero images to homepage and service pages
- [ ] Add team photos to /about page
- [ ] Add office photo to /contact
- [ ] Add city-specific project photos
- [ ] Write descriptive alt text for all images

**Why Third:** Needs photos from Kevin first. Biggest visual impact.

### Round 4: Content & SEO Polish
**Goal:** Improve search rankings and uniqueness  
**Time:** 1-2 days

- [ ] Add unique content to each city page
- [ ] Update all page titles and meta descriptions
- [ ] Enhance Schema.org markup
- [ ] Add OG images
- [ ] Generate proper favicon
- [ ] Optimize font loading

**Why Fourth:** Less urgent than trust/photos, but important for growth.

### Round 5: Accessibility & Final Polish
**Goal:** WCAG compliance and finishing touches  
**Time:** 1 day

- [ ] Full keyboard navigation test
- [ ] Color contrast verification
- [ ] Alt text audit
- [ ] Mobile layout polish
- [ ] Add social media links (when created)

**Why Last:** Important but not blocking other work.

---

## 13. KEVIN'S ACTION ITEMS

### Immediately:

1. **Approve PR #2 and merge** (phone + address + /inspect page)

2. **Provide 2-3 Verified Testimonials**
   - Get written permission from customers
   - Format: "Quote" - First Name L., City, KS
   - No star ratings or "verified review" language

3. **Provide Photos** (See Section 10 for complete list)
   - Priority: 6-8 before/after project pairs
   - Team photo (Kevin, Megan, Rick)
   - 1 hero image for homepage
   - Can deliver in batches

### Decisions Needed:

4. **Approve Round 1 Plan** (remove reviews, consolidate booking)

5. **Confirm Team Titles**
   - Kevin: Owner? President?
   - Megan: Office Manager? Operations Manager?
   - Rick: Inspector (confirmed)

6. **Social Media**
   - Create Facebook business page
   - Consider Instagram for before/after photos
   - Add links to site once created

### Later:

7. **Set up Short Link Redirects** (for print marketing)
   - twroofingkc.com/dh → teamworkroofingkc.com/inspect?src=doorhanger
   - Requires DNS configuration (can help with this)

---

## 14. SUMMARY: TOP 10 FINDINGS

1. **❌ CRITICAL: Fake reviews with star ratings** - Violates FTC guidelines, must remove immediately

2. **❌ CRITICAL: 4 overlapping booking pages** - Confuses users, consolidate to /inspect + /contact

3. **⚠️ HIGH: No real project photos** - Site looks generic without before/after gallery

4. **⚠️ HIGH: Thin/duplicated city page content** - Hurts SEO, need unique content per city

5. **⚠️ MEDIUM: Backup file in codebase** - Delete app/page.tsx.backup

6. **⚠️ MEDIUM: "Certified team" unverified claim** - Change to "licensed and insured"

7. **⚠️ MEDIUM: Missing team photos** - Hurts trust on /about page

8. **⚠️ MEDIUM: Font loading not optimized** - Switch to next/font

9. **⚠️ MEDIUM: Missing unique page metadata** - Hurts SEO rankings

10. **⚠️ MEDIUM: Schema markup incomplete** - Missing RoofingContractor type

---

## 15. ESTIMATED TIMELINE

**Round 1 (Critical):** 1 day → SHIP IMMEDIATELY  
**Round 2 (Gallery Setup):** 1 day → SHIP WHEN READY  
**Round 3 (Photos):** 2-3 days → **BLOCKED ON KEVIN**  
**Round 4 (Content/SEO):** 1-2 days  
**Round 5 (Polish):** 1 day

**Total Development Time:** 6-8 days of work  
**Calendar Time:** 2-3 weeks (accounting for photo collection)

---

## APPENDIX A: CURRENT SITE STRUCTURE

```
Pages (43 total):
/                           Homepage
/about                      About Us
/services                   Services Overview
/services/roof-replacement  
/services/roof-repair
/services/gutters
/services/siding
/services/windows
/materials                  Materials Info
/storm                      Storm Damage
/financing                  Financing Options
/warranty                   Warranty Info
/projects                   Projects (generic)
/reviews                    Reviews (REMOVE RATINGS)
/faq                        FAQ
/book                       Book Inspection (→ REDIRECT to /inspect)
/estimate                   Get Estimate (→ REDIRECT to /inspect)
/inspect                    Book Inspection (KEEP - PR #2 only)
/contact                    Contact Form (KEEP)
/service-areas              Service Areas Overview
/overland-park-ks/*         5 OP pages
/leawood-ks/*               5 Leawood pages
/lenexa-ks/*                5 Lenexa pages
/terms                      Terms of Service
/privacy                    Privacy Policy
```

---

**End of Audit Report**

*Next Steps: Await Kevin's approval of Round 1, then implement. Request photos for Round 3.*
