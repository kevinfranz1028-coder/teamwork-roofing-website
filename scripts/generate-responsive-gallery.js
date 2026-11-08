#!/usr/bin/env node

/**
 * Generate Responsive Gallery Images
 *
 * Creates 640/1280/2000 width variants in WebP and JPG
 * Never upscales (skips widths larger than source)
 * Strips all metadata for privacy
 */

const fs = require('fs')
const path = require('path')
const sharp = require('sharp')

const galleryDir = path.join(__dirname, '..', 'public', 'gallery')
const WIDTHS = [640, 1280, 2000]

async function processImage(inputPath, projectDir) {
  try {
    const img = sharp(inputPath)
    const metadata = await img.metadata()
    const sourceWidth = metadata.width

    const basename = path.basename(inputPath, path.extname(inputPath))

    console.log(`Processing ${basename} (source: ${sourceWidth}px)`)

    // Generate responsive sizes (never upscale)
    for (const width of WIDTHS) {
      if (width >= sourceWidth) {
        console.log(`  Skipping ${width}px (would upscale from ${sourceWidth}px)`)
        continue
      }

      // WebP variant
      await sharp(inputPath)
        .resize(width, null, { withoutEnlargement: true })
        .webp({ quality: 85 })
        .toFile(path.join(projectDir, `${basename}-${width}w.webp`))
      console.log(`  ✓ ${width}w.webp`)

      // JPG variant
      await sharp(inputPath)
        .resize(width, null, { withoutEnlargement: true })
        .jpeg({ quality: 85, mozjpeg: true })
        .toFile(path.join(projectDir, `${basename}-${width}w.jpg`))
      console.log(`  ✓ ${width}w.jpg`)
    }

    return true
  } catch (error) {
    console.error(`Error processing ${inputPath}:`, error.message)
    return false
  }
}

async function main() {
  console.log('🖼️  Generating responsive gallery images...\n')

  // Find all project directories
  const entries = fs.readdirSync(galleryDir, { withFileTypes: true })

  for (const entry of entries) {
    if (!entry.isDirectory() || entry.name === 'placeholder') continue

    const projectDir = path.join(galleryDir, entry.name)
    const files = fs.readdirSync(projectDir)

    // Find original JPGs (those without -640w, -1280w, -2000w suffix)
    const originals = files.filter(f =>
      f.endsWith('.jpg') &&
      !f.includes('-640w') &&
      !f.includes('-1280w') &&
      !f.includes('-2000w')
    )

    if (originals.length === 0) continue

    console.log(`\n📁 ${entry.name}`)
    console.log(`   Found ${originals.length} original images\n`)

    for (const original of originals) {
      await processImage(path.join(projectDir, original), projectDir)
    }
  }

  console.log('\n✅ Done generating responsive images')
}

main().catch(err => {
  console.error('Fatal error:', err)
  process.exit(1)
})
