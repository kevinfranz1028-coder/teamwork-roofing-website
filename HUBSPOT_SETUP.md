# HubSpot CRM Integration Setup Guide

This guide will walk you through completing the HubSpot integration for Teamwork Roofing's website.

## Overview

HubSpot tracking and forms have been integrated into three key pages:
- **Book Inspection** (`/book`)
- **Get Estimate** (`/estimate`)
- **Contact Us** (`/contact`)

All forms automatically capture hidden metadata including page URL, city detection, service interest, and lead source.

---

## Step 1: Create Forms in HubSpot

You need to create **3 forms** in your HubSpot account (Portal ID: 244741088).

### For Each Form:

1. **Log into HubSpot** → Navigate to **Marketing** → **Forms**
2. **Click "Create Form"** → Select **Embedded Form**
3. **Add the following visible fields** (in this order):

   **All 3 Forms Need:**
   - First Name (required)
   - Last Name (required)
   - Phone Number (required)
   - Email (optional but recommended)
   - Service Interest (dropdown with options):
     - Roof Replacement
     - Roof Repair
     - Storm Damage
     - Gutters
     - Siding
     - Windows
     - Full Exterior
     - Not Sure
   - Notes/Message (multi-line text)

4. **Add Hidden Fields** (these auto-populate from the website):
   - `page_url` (Single-line text)
   - `page_path` (Single-line text)
   - `city` (Single-line text)
   - `lead_source` (Single-line text)

   **Important:** Hidden fields must be created as custom properties in HubSpot first:
   - Go to **Settings** → **Data Management** → **Properties** → **Contact Properties**
   - Click **Create Property**
   - For each field, use type "Single-line text" and use the exact names above

5. **Configure Form Options:**
   - Set the form name to one of:
     - "Book Inspection Form"
     - "Estimate Request Form"
     - "Contact Form"
   - Turn OFF the built-in redirect (the website handles success states)
   - Customize the submit button text if desired

6. **Save the form**

---

## Step 2: Get Form GUIDs

For each of the 3 forms you created:

1. Click on the form in HubSpot
2. Click **"Share"** → **"Embed"**
3. Look for the embed code that looks like this:

```html
<script charset="utf-8" type="text/javascript" src="//js.hsforms.net/forms/embed/v2.js"></script>
<script>
  hbspt.forms.create({
    region: "na2",
    portalId: "244741088",
    formId: "XXXXXXXX-XXXX-XXXX-XXXX-XXXXXXXXXXXX"  ← THIS IS YOUR FORM GUID
  });
</script>
```

4. **Copy the `formId` value** (it's a GUID that looks like: `a1b2c3d4-e5f6-g7h8-i9j0-k1l2m3n4o5p6`)

---

## Step 3: Add Form GUIDs to Environment Variables

### For Local Development:

1. Open the `.env.local` file in the project root
2. Replace the `REPLACE_ME` placeholders with your actual Form GUIDs:

```bash
# HubSpot Configuration
NEXT_PUBLIC_HUBSPOT_PORTAL_ID=244741088
NEXT_PUBLIC_HUBSPOT_REGION=na2

# Replace these with your actual Form GUIDs from HubSpot:
NEXT_PUBLIC_HUBSPOT_FORM_ID_BOOK=your-book-form-guid-here
NEXT_PUBLIC_HUBSPOT_FORM_ID_ESTIMATE=your-estimate-form-guid-here
NEXT_PUBLIC_HUBSPOT_FORM_ID_CONTACT=your-contact-form-guid-here
```

3. **Save the file**
4. **Restart your development server** (`npm run dev`)

### For Production (Cloudflare Pages):

1. Log into your **Cloudflare Dashboard**
2. Go to **Pages** → Select your project
3. Go to **Settings** → **Environment Variables**
4. Add the following variables (for **Production** environment):

| Variable Name | Value |
|---------------|-------|
| `NEXT_PUBLIC_HUBSPOT_PORTAL_ID` | `244741088` |
| `NEXT_PUBLIC_HUBSPOT_REGION` | `na2` |
| `NEXT_PUBLIC_HUBSPOT_FORM_ID_BOOK` | `your-book-form-guid` |
| `NEXT_PUBLIC_HUBSPOT_FORM_ID_ESTIMATE` | `your-estimate-form-guid` |
| `NEXT_PUBLIC_HUBSPOT_FORM_ID_CONTACT` | `your-contact-form-guid` |

5. **Save and redeploy** your site

---

## Step 4: Test the Integration

### Test Tracking:

1. Visit your website
2. Open browser DevTools (F12) → **Console** tab
3. Look for HubSpot tracking messages (should see `_hsq` array loading)
4. Navigate between pages - each route change should log a virtual pageview

### Test Forms:

1. Visit each of the 3 pages:
   - `/book`
   - `/estimate`
   - `/contact`

2. **Check that forms load:**
   - You should see the HubSpot form render
   - Forms should match your site's styling (blue focus states, rounded corners)
   - If you see "REPLACE_ME" or no form appears, check your environment variables

3. **Submit a test form:**
   - Fill out the form with test data
   - Submit it
   - You should see a success message on the page

4. **Verify in HubSpot:**
   - Go to **Contacts** → **Contacts** in HubSpot
   - Find your test submission
   - Check that all hidden fields were captured:
     - `page_url` should show the full URL
     - `page_path` should show the route (e.g., `/book`)
     - `city` should show detected city (e.g., "Overland Park, KS" if URL had `/overland-park-ks/`)
     - `lead_source` should show "Website"
     - `service_interest` should show the auto-detected service

---

## How Auto-Detection Works

The integration automatically detects contextual information:

### City Detection:
- If URL contains `/overland-park-ks/` → City: "Overland Park, KS"
- If URL contains `/leawood-ks/` → City: "Leawood, KS"
- If URL contains `/lenexa-ks/` → City: "Lenexa, KS"
- If URL contains `/olathe-ks/` → City: "Olathe, KS"
- If URL contains `/shawnee-ks/` → City: "Shawnee, KS"
- Otherwise → City: "Kansas City Metro"

### Service Interest Detection:
- If URL contains `/roof-replacement` → "Roof Replacement"
- If URL contains `/roof-repair` → "Roof Repair"
- If URL contains `/storm` → "Storm Damage"
- If URL contains `/gutters` → "Gutters"
- If URL contains `/siding` → "Siding"
- If URL contains `/windows` → "Windows"
- On `/book` page → "Inspection Request"
- On `/estimate` page → "Quote Request"
- On `/contact` page → "General Inquiry"

---

## Troubleshooting

### Forms Not Appearing:
1. Check browser console for errors
2. Verify Form GUIDs are correct (no typos)
3. Ensure environment variables start with `NEXT_PUBLIC_`
4. Restart dev server after changing `.env.local`
5. Clear browser cache

### Hidden Fields Not Capturing:
1. Verify the custom properties exist in HubSpot with exact names:
   - `page_url`
   - `page_path`
   - `city`
   - `lead_source`
2. Ensure the fields are added to each form as **hidden fields**

### Tracking Not Working:
1. Check that the tracking script loads (view page source, search for `hs-scripts.com`)
2. Verify Portal ID is correct (244741088)
3. Check browser console for HubSpot errors
4. Ensure ad blockers aren't blocking HubSpot scripts

### Form Styling Issues:
- Forms automatically inherit your site's Tailwind styling
- If styling looks off, check that Tailwind CSS is properly loaded on the page

---

## Files Modified

Here's what was changed in your codebase:

### New Components:
- `components/HubSpotFormEmbed.tsx` - Reusable form embed component
- `components/HubSpotTracking.tsx` - Route change tracking
- `components/forms/BookInspectionForm.tsx` - Book page form wrapper
- `components/forms/EstimateForm.tsx` - Estimate page form wrapper
- `components/forms/ContactForm.tsx` - Contact page form wrapper

### Updated Pages:
- `app/layout.tsx` - Added tracking script + tracking component
- `app/book/page.tsx` - Replaced HTML form with HubSpot form
- `app/estimate/page.tsx` - Replaced HTML form with HubSpot form
- `app/contact/page.tsx` - Replaced HTML form with HubSpot form

### Configuration:
- `.env.local` - Environment variables (local development)
- `.env.local.example` - Template for environment variables

---

## Support

If you run into issues:
1. Check the browser console for JavaScript errors
2. Verify all Form GUIDs are correct in `.env.local` or Cloudflare environment variables
3. Ensure custom properties are created in HubSpot before adding as hidden fields
4. Test in an incognito window to rule out browser extensions/cache

**HubSpot Resources:**
- [HubSpot Forms Documentation](https://developers.hubspot.com/docs/api/marketing/forms)
- [Creating Custom Properties](https://knowledge.hubspot.com/properties/create-and-edit-properties)
- [Embed Forms Guide](https://knowledge.hubspot.com/forms/embed-a-form-on-an-external-site)
