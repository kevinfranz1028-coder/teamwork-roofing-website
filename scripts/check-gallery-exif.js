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

const galleryDir = path.join(__dirname, '..', 'public', 'gallery')

// Check if gallery directory exists and has actual image files (not just placeholder)
function hasActualImages(dir) {
  if (!fs.existsSync(dir)) return false

  const entries = fs.readdirSync(dir, { withFileTypes: true })
  for (const entry of entries) {
    if (entry.isDirectory() && entry.name !== 'placeholder') {
      return true // Found a project directory (not placeholder)
    }
  }
  return false
}

// Only require exif-parser if we have actual images to check
let exifParser
if (hasActualImages(galleryDir)) {
  try {
    exifParser = require('exif-parser')
  } catch (e) {
    console.error('❌ Error: exif-parser not installed')
    console.error('   Gallery contains images but exif-parser is missing')
    console.error('   Run: npm install exif-parser')
    process.exit(1)
  }
}

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

    return { hasExif, hasGPS, tags: result.tags, readable: true }
  } catch (e) {
    // FAIL CLOSED: Any image that cannot be parsed is a failure
    // This includes:
    // - Corrupted files
    // - Unsupported formats
    // - Files that cannot be read
    // Only explicitly allowlisted SVG placeholders are exempt (handled in scan)
    return { hasExif: false, hasGPS: false, tags: {}, readable: false, error: e.message }
  }
}

function scanDirectory(dir) {
  const violations = []

  if (!fs.existsSync(dir)) {
    console.log('✓ No gallery directory found (no images to check)')
    return violations
  }

  if (!hasActualImages(dir)) {
    console.log('✓ No gallery images to check (only placeholder files)')
    return violations
  }

  function scan(currentDir) {
    const entries = fs.readdirSync(currentDir, { withFileTypes: true })

    for (const entry of entries) {
      const fullPath = path.join(currentDir, entry.name)

      if (entry.isDirectory()) {
        // Skip placeholder directory
        if (entry.name === 'placeholder') continue
        scan(fullPath)
      } else if (entry.isFile()) {
        // Check image files (skip SVG placeholders)
        const ext = path.extname(entry.name).toLowerCase()
        if (['.jpg', '.jpeg', '.webp', '.png', '.heic'].includes(ext)) {
          const result = checkImageForExif(fullPath)
          const relativePath = path.relative(galleryDir, fullPath)

          // FAIL CLOSED: Unreadable images are violations
          if (!result.readable) {
            violations.push({
              file: relativePath,
              type: 'UNREADABLE',
              error: result.error
            })
          } else if (result.hasGPS) {
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
  console.error('❌ FAIL: Found violations in gallery images\n')

  const hasUnreadable = violations.some(v => v.type === 'UNREADABLE')
  const hasPrivacy = violations.some(v => v.type === 'GPS' || v.type === 'EXIF')

  if (hasPrivacy) {
    console.error('PRIVACY VIOLATION: The following images contain metadata:\n')
  }
  if (hasUnreadable) {
    console.error('UNREADABLE IMAGES: The following images cannot be parsed (FAIL CLOSED):\n')
  }

  violations.forEach(v => {
    console.error(`  ⚠️  ${v.file}`)
    console.error(`      Type: ${v.type}`)
    if (v.type === 'GPS') {
      console.error('      ** GPS COORDINATES FOUND **')
      if (v.tags.GPSLatitude) console.error(`      Latitude: ${v.tags.GPSLatitude}`)
      if (v.tags.GPSLongitude) console.error(`      Longitude: ${v.tags.GPSLongitude}`)
    } else if (v.type === 'UNREADABLE') {
      console.error(`      Error: ${v.error}`)
      console.error('      ** IMAGE CANNOT BE VERIFIED **')
    }
    console.error('')
  })

  console.error('REQUIRED ACTIONS:')
  if (hasPrivacy) {
    console.error('- Re-process images with scripts/process-gallery-images.js')
    console.error('- Verify images are stripped: npm run check:gallery')
    console.error('- Do NOT commit images with EXIF/GPS data')
  }
  if (hasUnreadable) {
    console.error('- Unreadable images must be replaced or removed')
    console.error('- Only valid JPEG/PNG/WebP files are allowed')
    console.error('- Corrupted or unsupported files are rejected (fail-closed policy)')
  }
  console.error('')

  process.exit(1)
}
