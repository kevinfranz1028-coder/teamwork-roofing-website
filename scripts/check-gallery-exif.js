#!/usr/bin/env node

/**
 * Gallery EXIF/GPS Check Script (Fail-Closed)
 *
 * Scans ALL files in public/gallery/ for privacy-sensitive EXIF/GPS metadata.
 * FAILS the build if:
 * - Any GPS data is found
 * - Any sensitive EXIF data is found (dates, camera info, maker notes, etc.)
 * - Any file is unreadable/corrupted
 * - Any file has an extension not in the allowed list
 *
 * Benign JFIF metadata (resolution, version) is allowed.
 *
 * USAGE:
 *   npm run check:gallery
 *
 * REQUIREMENTS:
 *   npm install sharp  (supports JPEG, PNG, WebP, HEIC)
 */

const fs = require('fs')
const path = require('path')

// Load sharp (supports JPEG, PNG, WebP, HEIC)
let sharp
try {
  sharp = require('sharp')
} catch (e) {
  console.error('❌ Error: sharp not installed')
  console.error('   Run: npm install sharp')
  process.exit(1)
}

const galleryDir = path.join(__dirname, '..', 'public', 'gallery')

// ALLOWED image extensions (fail-closed: anything else fails)
const ALLOWED_EXTENSIONS = ['.jpg', '.jpeg', '.webp', '.png', '.heic']

// SPECIFIC allowlisted placeholder paths (fail-closed: only these exact paths are exempt)
const ALLOWLISTED_PLACEHOLDERS = [
  'placeholder/placeholder.svg'
]

// BENIGN metadata fields that are NOT privacy violations
const BENIGN_FIELDS = new Set([
  'JFIFVersion',
  'ResolutionUnit',
  'XResolution',
  'YResolution',
  'ThumbnailWidth',
  'ThumbnailHeight',
  'ColorSpace',
  'ColorComponents',
  'Subsampling'
])

/**
 * Check if a path is an allowlisted placeholder
 */
function isAllowlistedPlaceholder(relativePath) {
  return ALLOWLISTED_PLACEHOLDERS.some(allowed => relativePath === allowed)
}

/**
 * Check if metadata contains only benign fields
 */
function isBenignMetadata(data) {
  if (!data || Object.keys(data).length === 0) {
    return true // No metadata is fine
  }
  
  // Check if all fields are benign
  const fields = Object.keys(data)
  return fields.every(field => BENIGN_FIELDS.has(field))
}

/**
 * Check image for EXIF/GPS data using sharp
 * Returns: { readable, hasExif, hasGPS, tags, error }
 */
async function checkImageForExif(filePath) {
  try {
    // Read metadata using sharp (supports JPEG, PNG, WebP, HEIC)
    const metadata = await sharp(filePath).metadata()

    // Extract all metadata fields
    const data = {
      ...metadata.exif,
      ...metadata.iptc,
      ...metadata.xmp,
      ...metadata.icc
    }

    // Check for GPS data specifically
    const hasGPS = data && (
      data.latitude !== undefined ||
      data.longitude !== undefined ||
      data.GPSLatitude !== undefined ||
      data.GPSLongitude !== undefined ||
      data.GPSAltitude !== undefined
    )

    // Check for sensitive EXIF data (excluding benign JFIF fields)
    const hasSensitiveExif = data && Object.keys(data).length > 0 && !isBenignMetadata(data)

    return {
      readable: true,
      hasExif: hasSensitiveExif,
      hasGPS,
      tags: data || {}
    }
  } catch (e) {
    // FAIL CLOSED: unreadable images are violations
    return {
      readable: false,
      hasExif: false,
      hasGPS: false,
      tags: {},
      error: e.message
    }
  }
}

/**
 * Scan directory for violations
 */
async function scanDirectory(dir) {
  const violations = []
  
  if (!fs.existsSync(dir)) {
    console.log('✓ No gallery directory found (no images to check)')
    return violations
  }
  
  async function scan(currentDir) {
    const entries = fs.readdirSync(currentDir, { withFileTypes: true })
    
    for (const entry of entries) {
      const fullPath = path.join(currentDir, entry.name)
      const relativePath = path.relative(galleryDir, fullPath)
      
      if (entry.isDirectory()) {
        await scan(fullPath)
      } else if (entry.isFile()) {
        const ext = path.extname(entry.name).toLowerCase()
        
        // Check if this is an allowlisted placeholder
        if (isAllowlistedPlaceholder(relativePath)) {
          continue // Skip allowlisted placeholders
        }
        
        // FAIL CLOSED: Any file with extension not in allowed list fails
        if (!ALLOWED_EXTENSIONS.includes(ext) && ext !== '.svg') {
          violations.push({
            file: relativePath,
            type: 'DISALLOWED_EXTENSION',
            extension: ext
          })
          continue
        }
        
        // SVGs that aren't allowlisted fail
        if (ext === '.svg') {
          violations.push({
            file: relativePath,
            type: 'DISALLOWED_SVG',
            message: 'Only specific allowlisted placeholder SVGs are permitted'
          })
          continue
        }
        
        // Check images for EXIF/GPS
        if (ALLOWED_EXTENSIONS.includes(ext)) {
          const result = await checkImageForExif(fullPath)
          
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
  
  await scan(dir)
  return violations
}

// Main
async function main() {
  console.log('🔍 Checking gallery images for EXIF/GPS metadata...\n')
  
  const violations = await scanDirectory(galleryDir)
  
  if (violations.length === 0) {
    console.log('✅ PASS: No EXIF/GPS data found in gallery images')
    console.log('   All images are safe to publish (privacy protected)')
    process.exit(0)
  } else {
    console.error('❌ FAIL: Found violations in gallery images\n')
    
    const hasPrivacy = violations.some(v => v.type === 'GPS' || v.type === 'EXIF')
    const hasUnreadable = violations.some(v => v.type === 'UNREADABLE')
    const hasDisallowed = violations.some(v => v.type === 'DISALLOWED_EXTENSION' || v.type === 'DISALLOWED_SVG')
    
    if (hasPrivacy) {
      console.error('PRIVACY VIOLATION: The following images contain metadata:\n')
    }
    if (hasUnreadable) {
      console.error('UNREADABLE IMAGES: The following images cannot be parsed (FAIL CLOSED):\n')
    }
    if (hasDisallowed) {
      console.error('DISALLOWED FILES: The following files are not permitted:\n')
    }
    
    violations.forEach(v => {
      console.error(`  ⚠️  ${v.file}`)
      console.error(`      Type: ${v.type}`)
      if (v.type === 'GPS') {
        console.error('      ** GPS COORDINATES FOUND **')
        if (v.tags.latitude) console.error(`      Latitude: ${v.tags.latitude}`)
        if (v.tags.longitude) console.error(`      Longitude: ${v.tags.longitude}`)
        if (v.tags.GPSLatitude) console.error(`      GPSLatitude: ${v.tags.GPSLatitude}`)
        if (v.tags.GPSLongitude) console.error(`      GPSLongitude: ${v.tags.GPSLongitude}`)
      } else if (v.type === 'UNREADABLE') {
        console.error(`      Error: ${v.error}`)
        console.error('      ** IMAGE CANNOT BE VERIFIED **')
      } else if (v.type === 'DISALLOWED_EXTENSION') {
        console.error(`      Extension: ${v.extension}`)
        console.error('      ** FILE TYPE NOT ALLOWED **')
      } else if (v.type === 'DISALLOWED_SVG') {
        console.error(`      ${v.message}`)
      } else if (v.type === 'EXIF') {
        console.error('      ** SENSITIVE EXIF METADATA FOUND **')
        console.error(`      Fields: ${Object.keys(v.tags).join(', ')}`)
      }
      console.error('')
    })
    
    console.error('REQUIRED ACTIONS:')
    if (hasPrivacy) {
      console.error('- Re-process images to remove EXIF/GPS metadata')
      console.error('- Verify images are stripped: npm run check:gallery')
      console.error('- Do NOT commit images with EXIF/GPS data')
    }
    if (hasUnreadable) {
      console.error('- Unreadable images must be replaced or removed')
      console.error('- Only valid JPEG/PNG/WebP files are allowed')
      console.error('- Corrupted or unsupported files are rejected (fail-closed policy)')
    }
    if (hasDisallowed) {
      console.error('- Remove files with disallowed extensions')
      console.error('- Only .jpg, .jpeg, .webp, .png, .heic are permitted')
      console.error('- SVG files must be explicitly allowlisted in the script')
    }
    console.error('')
    
    process.exit(1)
  }
}

main().catch(err => {
  console.error('Fatal error:', err)
  process.exit(1)
})
