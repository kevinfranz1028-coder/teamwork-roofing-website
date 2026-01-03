# Deployment Guide

This guide will walk you through deploying the Teamwork Roofing website to Cloudflare Pages.

## Prerequisites

1. A GitHub account
2. A Cloudflare account (free tier works)
3. Your repository pushed to GitHub

## Step 1: Push to GitHub

1. Create a new repository on GitHub
2. Initialize git in your project:
```bash
git init
git add .
git commit -m "Initial commit - Teamwork Roofing website"
git branch -M main
git remote add origin <your-github-repo-url>
git push -u origin main
```

## Step 2: Connect Cloudflare Pages

1. Log in to [Cloudflare Dashboard](https://dash.cloudflare.com)
2. Click "Workers & Pages" in the left sidebar
3. Click "Create application" → "Pages" → "Connect to Git"
4. Authorize GitHub and select your repository
5. Click "Begin setup"

## Step 3: Configure Build Settings

Set the following configuration:

- **Project name:** `teamwork-roofing` (or your preference)
- **Production branch:** `main`
- **Framework preset:** Next.js
- **Build command:** `npm run build`
- **Build output directory:** `out`
- **Root directory:** `/`
- **Node version:** `18` or higher

## Step 4: Environment Variables (Optional)

If you want email/SMS notifications for leads, add these environment variables:

1. Click "Add variable" in the build settings
2. Add:
   - `RESEND_API_KEY` - Get from [Resend.com](https://resend.com)
   - `TWILIO_ACCOUNT_SID` - Get from [Twilio.com](https://twilio.com)
   - `TWILIO_AUTH_TOKEN` - Get from [Twilio.com](https://twilio.com)

## Step 5: Deploy

1. Click "Save and Deploy"
2. Wait 2-3 minutes for the build to complete
3. Your site will be live at `https://teamwork-roofing.pages.dev`

## Step 6: Custom Domain (Recommended)

1. In Cloudflare Pages, go to your project
2. Click "Custom domains"
3. Click "Set up a custom domain"
4. Enter your domain (e.g., `teamworkroofing.com`)
5. Follow the DNS instructions to point your domain to Cloudflare

### If Your Domain is Already on Cloudflare:
- DNS records will be added automatically
- SSL certificate will be provisioned automatically

### If Your Domain is Elsewhere:
- Update your nameservers to Cloudflare's nameservers
- Or add a CNAME record pointing to your Pages URL

## Step 7: Enable Form Notifications

To receive notifications when someone submits a form:

### Email Notifications (Resend)

1. Sign up at [Resend.com](https://resend.com)
2. Verify your domain or use their test domain
3. Get your API key
4. Add `RESEND_API_KEY` to Cloudflare Pages environment variables
5. Uncomment the Resend code in `functions/api/lead.ts`
6. Update the email addresses in the code

### SMS Notifications (Twilio)

1. Sign up at [Twilio.com](https://twilio.com)
2. Get a phone number
3. Get your Account SID and Auth Token
4. Add both to Cloudflare Pages environment variables
5. Uncomment the Twilio code in `functions/api/lead.ts`
6. Update the phone numbers in the code

## Step 8: Testing

1. Visit your deployed site
2. Test the estimate form
3. Test the booking form
4. Test the contact form
5. Verify forms submit successfully
6. Check that you receive notifications (if configured)

## Automatic Deployments

Every time you push to the `main` branch:
1. Cloudflare Pages will automatically rebuild your site
2. Changes go live in 2-3 minutes
3. You'll get a notification when deployment completes

## Preview Deployments

Every pull request gets its own preview URL:
- Test changes before merging
- Share with clients for approval
- Automatic cleanup after merge

## Monitoring

In the Cloudflare Pages dashboard, you can see:
- Build logs
- Deployment history
- Analytics (traffic, performance)
- Function logs (for form submissions)

## Rollback

If something breaks:
1. Go to Cloudflare Pages dashboard
2. Click "Deployments"
3. Find a working deployment
4. Click "Rollback to this deployment"

## Performance Tips

Your site will be automatically optimized by Cloudflare:
- Global CDN (fast everywhere)
- Automatic HTTPS
- DDoS protection
- Analytics included

## Troubleshooting

### Build fails
- Check build logs in Cloudflare dashboard
- Verify `package.json` is correct
- Ensure Node version is 18+

### Forms not working
- Check Functions logs in Cloudflare dashboard
- Verify function code in `functions/api/lead.ts`
- Check environment variables are set

### Custom domain not working
- Verify DNS records are correct
- Wait up to 24 hours for DNS propagation
- Check SSL certificate status

## Next Steps

1. Add your logo and real images
2. Update content with your actual reviews and projects
3. Configure email/SMS notifications
4. Set up Google Analytics (add to `app/layout.tsx`)
5. Test on mobile devices
6. Share with your team

## Support

- Cloudflare Pages Docs: https://developers.cloudflare.com/pages
- Next.js Docs: https://nextjs.org/docs
- Tailwind CSS Docs: https://tailwindcss.com/docs

---

Need help? Call 913-396-3717
