#!/usr/bin/env node

/**
 * Gallery Image Processing Script
 *
 * Processes raw project photos for the gallery:
 * - Strips ALL EXIF/GPS metadata for privacy
 * - Auto-orients images
 * - Generates optimized web sizes (large + thumbnail)
 * - Outputs as WebP + JPEG fallback
 *
 * USAGE:
 *   node scripts/process-gallery-images.js <project-id> <input-folder>
 *
 * EXAMPLE:
 *   node scripts/process-gallery-images.js op-001 ~/Desktop/project-photos/overland-park-001
 *
 * REQUIREMENTS:
 *   npm install sharp
 *
 * See docs/GALLERY.md for complete photo guidelines
 */

const sharp = require('sharp')
const fs = require('fs')
const path = require('path')

// Configuration
const SIZES = {
  large: { width: 1200, height: 900 },
  thumb: { width: 400, height: 300 }
}

const QUALITY = {
  webp: 85,
  jpeg: 90
}

async function processImage(inputPath, outputDir, basename, size) {
  const sizeConfig = SIZES[size]

  // Process image
  const image = sharp(inputPath)
    .rotate() // Auto-orient based on EXIF
    .resize(sizeConfig.width, sizeConfig.height, {
      fit: 'cover',
      position: 'center'
    })
    .withMetadata({}) // Strip ALL metadata (EXIF, GPS, etc.)

  // Output WebP
  await image
    .clone()
    .webp({ quality: QUALITY.webp })
    .toFile(path.join(outputDir, `${basename}-${size}.webp`))

  // Output JPEG fallback
  await image
    .clone()
    .jpeg({ quality: QUALITY.jpeg, mozjpeg: true })
    .toFile(path.join(outputDir, `${basename}-${size}.jpg`))

  console.log(`  ✓ ${basename}-${size} (WebP + JPEG)`)
}

async function processProject(projectId, inputFolder) {
  console.log(`\nProcessing project: ${projectId}`)
  console.log(`Input folder: ${inputFolder}\n`)

  // Validate input folder
  if (!fs.existsSync(inputFolder)) {
    console.error(`❌ Error: Input folder not found: ${inputFolder}`)
    process.exit(1)
  }

  // Create output directory
  const outputDir = path.join(__dirname, '..', 'public', 'gallery', projectId)
  if (!fs.existsSync(outputDir)) {
    fs.mkdirSync(outputDir, { recursive: true })
  }

  // Find before/after images
  const files = fs.readdirSync(inputFolder)
  const beforeImage = files.find(f => f.toLowerCase().includes('before'))
  const afterImage = files.find(f => f.toLowerCase().includes('after'))

  if (!beforeImage || !afterImage) {
    console.error('❌ Error: Could not find before/after images.')
    console.error('   Image files must contain "before" or "after" in filename.')
    console.error(`   Found files: ${files.join(', ')}`)
    process.exit(1)
  }

  console.log('Processing images:')

  // Process before image
  const beforePath = path.join(inputFolder, beforeImage)
  await processImage(beforePath, outputDir, 'before', 'large')
  await processImage(beforePath, outputDir, 'before', 'thumb')

  // Process after image
  const afterPath = path.join(inputFolder, afterImage)
  await processImage(afterPath, outputDir, 'after', 'large')
  await processImage(afterPath, outputDir, 'after', 'thumb')

  console.log(`\n✅ Done! Images saved to: public/gallery/${projectId}/`)
  console.log('\nNext steps:')
  console.log(`1. Review images in public/gallery/${projectId}/`)
  console.log('2. Add project entry to content/gallery.ts')
  console.log('3. Update gallery paths to use the generated files')
  console.log('\nExample gallery entry:')
  console.log(`{
  id: "${projectId}",
  city: "Overland Park", // CHANGE THIS
  jobType: "full-replacement", // CHANGE THIS
  beforeImage: "/gallery/${projectId}/before-large.webp",
  afterImage: "/gallery/${projectId}/after-large.webp",
  beforeAlt: "Home before roof replacement", // WRITE DESCRIPTIVE ALT TEXT
  afterAlt: "Same home after roof replacement", // WRITE DESCRIPTIVE ALT TEXT
  description: "Full roof replacement - GAF shingles", // CHANGE THIS
  date: "2024-11", // CHANGE THIS
  featured: false
}`)
}

// Main
const args = process.argv.slice(2)

if (args.length < 2) {
  console.log('Usage: node scripts/process-gallery-images.js <project-id> <input-folder>')
  console.log('')
  console.log('Example:')
  console.log('  node scripts/process-gallery-images.js op-001 ~/Desktop/project-photos/overland-park-001')
  console.log('')
  console.log('The input folder should contain:')
  console.log('  - One "before" image (filename must contain "before")')
  console.log('  - One "after" image (filename must contain "after")')
  process.exit(1)
}

const [projectId, inputFolder] = args
processProject(projectId, inputFolder).catch(error => {
  console.error('❌ Error:', error.message)
  process.exit(1)
})
