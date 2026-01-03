# Quick Start Guide

Get your Teamwork Roofing website up and running in 5 steps.

## Step 1: Install Dependencies

```bash
npm install
```

## Step 2: Run Development Server

```bash
npm run dev
```

Visit http://localhost:3000 to see your site.

## Step 3: Customize Your Branding

### Update Phone Number
Search and replace `913-396-3717` with your actual phone number throughout the project.

### Add Your Logo
1. Add your logo to `public/logo.png`
2. Update the logo in `components/Header.tsx` and `components/Footer.tsx`

### Update Colors (Optional)
Edit `tailwind.config.js`:
```javascript
colors: {
  'teamwork-blue': '#0066CC',  // Change to your brand color
}
```

### Update Business Info
Edit `components/SchemaMarkup.tsx`:
- Business address
- GPS coordinates
- Business hours

## Step 4: Add Real Content

### Projects
Edit `app/projects/page.tsx` - Add your real project photos and details

### Reviews
Edit `app/reviews/page.tsx` - Add authentic customer reviews

### Images
Add images to `public/` directory:
- Hero images
- Project photos
- Before/after photos

## Step 5: Deploy to Cloudflare Pages

See DEPLOYMENT.md for complete instructions, or:

1. Push to GitHub:
```bash
git init
git add .
git commit -m "Initial commit"
git branch -M main
git remote add origin <your-repo-url>
git push -u origin main
```

2. Connect to Cloudflare Pages:
   - Go to dash.cloudflare.com
   - Workers & Pages → Create → Connect to Git
   - Select your repo
   - Build command: `npm run build`
   - Build output: `out`
   - Deploy!

## What's Included

All pages are ready:
- ✅ Homepage with all sections
- ✅ All service pages (Roofing, Gutters, Siding, Windows, Storm)
- ✅ Interactive estimate calculator
- ✅ Booking form
- ✅ Projects gallery
- ✅ Reviews page
- ✅ FAQ with categories
- ✅ Contact form
- ✅ About, Financing, Warranty pages
- ✅ Privacy & Terms pages
- ✅ SEO optimization
- ✅ Mobile responsive
- ✅ Dark mode design

## Next Steps

1. Test all forms
2. Add Google Analytics (optional)
3. Set up email/SMS notifications (see DEPLOYMENT.md)
4. Add your real project photos
5. Launch!

## Need Help?

Check these files:
- `README.md` - Full documentation
- `DEPLOYMENT.md` - Deployment guide
- `package.json` - Available commands

---

Built for Teamwork Roofing Services LLC
