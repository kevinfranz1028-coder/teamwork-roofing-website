# Teamwork Roofing Services Website

A modern, premium dark-mode website for Teamwork Roofing Services LLC built with Next.js, Tailwind CSS, and deployed on Cloudflare Pages.

## Features

- Bold premium dark-mode design
- Mobile-first responsive layout
- 19 pages including services, estimate calculator, booking form
- SEO optimized with schema markup and sitemap
- Cloudflare Pages Functions for form handling
- Photo-proof inspection emphasis
- Same-week inspection promise
- Teamwork financing integration ready

## Pages

- **Home** (`/`) - Hero, services, promise strip, projects, reviews, FAQ
- **Services** (`/services/`) - Service overview and routing
- **Roof Replacement** (`/services/roof-replacement/`)
- **Roof Repair** (`/services/roof-repair/`)
- **Gutters** (`/services/gutters/`)
- **Siding** (`/services/siding/`)
- **Windows** (`/services/windows/`)
- **Storm/Insurance** (`/storm/`) - Full exterior damage assessment
- **Estimate Hub** (`/estimate/`) - Interactive estimator with lead capture
- **Book Inspection** (`/book/`) - Same-week inspection booking
- **Financing** (`/financing/`)
- **Warranty** (`/warranty/`)
- **Projects** (`/projects/`) - Filterable project gallery
- **Reviews** (`/reviews/`)
- **FAQ** (`/faq/`) - Categorized accordion FAQ
- **About** (`/about/`)
- **Contact** (`/contact/`)
- **Privacy** (`/privacy/`)
- **Terms** (`/terms/`)

## Tech Stack

- **Framework:** Next.js 14 (Static Export)
- **Styling:** Tailwind CSS
- **Icons:** React Icons
- **Deployment:** Cloudflare Pages
- **Forms:** Cloudflare Pages Functions
- **SEO:** Next.js Metadata API, Schema.org markup

## Getting Started

### Prerequisites

- Node.js 18+
- npm or yarn

### Installation

1. Clone the repository:
```bash
git clone <your-repo-url>
cd teamwork-roofing-website
```

2. Install dependencies:
```bash
npm install
```

3. Run development server:
```bash
npm run dev
```

4. Open [http://localhost:3000](http://localhost:3000) in your browser

### Build

Build the static site for production:
```bash
npm run build
```

This creates an optimized static export in the `out/` directory.

## Deployment to Cloudflare Pages

### Method 1: GitHub Integration (Recommended)

1. Push your code to GitHub
2. Log in to [Cloudflare Dashboard](https://dash.cloudflare.com)
3. Go to Pages → Create a project → Connect to Git
4. Select your repository
5. Configure build settings:
   - **Build command:** `npm run build`
   - **Build output directory:** `out`
   - **Root directory:** `/`
6. Add environment variables (if using email/SMS notifications):
   - `RESEND_API_KEY` (for email notifications)
   - `TWILIO_ACCOUNT_SID` (for SMS notifications)
   - `TWILIO_AUTH_TOKEN` (for SMS notifications)
7. Deploy!

### Method 2: Wrangler CLI

1. Install Wrangler:
```bash
npm install -g wrangler
```

2. Login to Cloudflare:
```bash
wrangler login
```

3. Build and deploy:
```bash
npm run build
wrangler pages deploy out --project-name=teamwork-roofing
```

## Environment Variables

For production, configure these in Cloudflare Pages settings:

```
RESEND_API_KEY=your_resend_api_key
TWILIO_ACCOUNT_SID=your_twilio_sid
TWILIO_AUTH_TOKEN=your_twilio_token
```

## Form Handling

Forms currently log to console. To enable email/SMS notifications:

1. Sign up for [Resend](https://resend.com) (email) and/or [Twilio](https://twilio.com) (SMS)
2. Add API keys to Cloudflare Pages environment variables
3. Uncomment the email/SMS code in `functions/api/lead.ts`

## Customization

### Branding

- **Colors:** Edit `tailwind.config.js` to change `teamwork-blue` and dark theme colors
- **Logo:** Add your logo image and update references in `components/Header.tsx` and `components/Footer.tsx`
- **Phone Number:** Global search/replace `913-396-3717` with your number
- **Service Area:** Update service area text in Header, Footer, and relevant pages

### Content

- **Reviews:** Update reviews in `app/reviews/page.tsx` and homepage
- **Projects:** Add real project data in `app/projects/page.tsx`
- **FAQ:** Customize questions in `app/faq/page.tsx`
- **Pricing:** Adjust estimator logic in `app/estimate/page.tsx`

### Images

Add your images to the `public/` directory:
- `/public/logo.png` - Your logo
- `/public/projects/` - Project photos
- `/public/hero.jpg` - Hero image

Update image references throughout the site.

## SEO

The site includes:
- Meta tags on all pages
- Open Graph tags
- Sitemap at `/sitemap.xml`
- Robots.txt
- LocalBusiness schema markup
- Clean URLs with trailing slashes

### Update Schema Markup

Edit `components/SchemaMarkup.tsx` to add:
- Your business address
- Correct GPS coordinates
- Business hours
- Additional service areas

## Performance

This site uses:
- Static generation for fast loading
- Image optimization (when real images are added)
- Minimal JavaScript
- Cloudflare CDN for global performance

## Support

For questions or issues:
- Email: [your-email]
- Phone: 913-396-3717

## License

Proprietary - Teamwork Roofing Services LLC

---

Built with the Teamwork philosophy: partnership, transparency, and quality.
