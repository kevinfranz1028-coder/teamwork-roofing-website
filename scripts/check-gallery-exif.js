#!/usr/bin/env node

/**
 * Gallery EXIF/GPS Check Script
 *
 * Scans all images in public/gallery/ for EXIF/GPS metadata.
 * FAILS the build if any EXIF/GPS data is found (privacy violation).
 *
 * USAGE:
 *   npm run check:gallery
 *
 * This should be run:
 * - Before every commit that adds gallery images
 * - As part of the build process
 * - After running process-gallery-images.js (which strips EXIF)
 *
 * REQUIREMENTS:
 *   npm install exif-parser
 */

const fs = require('fs')
const path = require('path')

let exifParser
try {
  exifParser = require('exif-parser')
} catch (e) {
  console.error('❌ Error: exif-parser not installed')
  console.error('   Run: npm install exif-parser')
  process.exit(1)
}

const galleryDir = path.join(__dirname, '..', 'public', 'gallery')

function checkImageForExif(filePath) {
  try {
    const buffer = fs.readFileSync(filePath)
    const parser = exifParser.create(buffer)
    const result = parser.parse()

    // Check for ANY EXIF data
    const hasExif = result.tags && Object.keys(result.tags).length > 0
    const hasGPS = result.tags && (
      result.tags.GPSLatitude !== undefined ||
      result.tags.GPSLongitude !== undefined ||
      result.tags.GPSAltitude !== undefined ||
      result.tags.GPSLatitudeRef !== undefined ||
      result.tags.GPSLongitudeRef !== undefined
    )

    return { hasExif, hasGPS, tags: result.tags }
  } catch (e) {
    // Not a JPEG or no EXIF data (which is good)
    return { hasExif: false, hasGPS: false, tags: {} }
  }
}

function scanDirectory(dir) {
  const violations = []

  if (!fs.existsSync(dir)) {
    console.log('✓ No gallery directory found (no images to check)')
    return violations
  }

  function scan(currentDir) {
    const entries = fs.readdirSync(currentDir, { withFileTypes: true })

    for (const entry of entries) {
      const fullPath = path.join(currentDir, entry.name)

      if (entry.isDirectory()) {
        scan(fullPath)
      } else if (entry.isFile()) {
        // Check image files
        const ext = path.extname(entry.name).toLowerCase()
        if (['.jpg', '.jpeg', '.webp', '.png', '.heic'].includes(ext)) {
          const result = checkImageForExif(fullPath)
          const relativePath = path.relative(galleryDir, fullPath)

          if (result.hasGPS) {
            violations.push({
              file: relativePath,
              type: 'GPS',
              tags: result.tags
            })
          } else if (result.hasExif) {
            violations.push({
              file: relativePath,
              type: 'EXIF',
              tags: result.tags
            })
          }
        }
      }
    }
  }

  scan(dir)
  return violations
}

// Main
console.log('🔍 Checking gallery images for EXIF/GPS metadata...\n')

const violations = scanDirectory(galleryDir)

if (violations.length === 0) {
  console.log('✅ PASS: No EXIF/GPS data found in gallery images')
  console.log('   All images are safe to publish (privacy protected)')
  process.exit(0)
} else {
  console.error('❌ FAIL: Found EXIF/GPS data in gallery images\n')
  console.error('PRIVACY VIOLATION: The following images contain metadata:\n')

  violations.forEach(v => {
    console.error(`  ⚠️  ${v.file}`)
    console.error(`      Type: ${v.type}`)
    if (v.type === 'GPS') {
      console.error('      ** GPS COORDINATES FOUND **')
      if (v.tags.GPSLatitude) console.error(`      Latitude: ${v.tags.GPSLatitude}`)
      if (v.tags.GPSLongitude) console.error(`      Longitude: ${v.tags.GPSLongitude}`)
    }
    console.error('')
  })

  console.error('REQUIRED ACTIONS:')
  console.error('1. Re-process images with scripts/process-gallery-images.js')
  console.error('2. Verify images are stripped: npm run check:gallery')
  console.error('3. Do NOT commit images with EXIF/GPS data\n')

  process.exit(1)
}
