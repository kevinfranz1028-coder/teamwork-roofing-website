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

// Load exifr for decoding EXIF bytes
let exifr
try {
  exifr = require('exifr')
} catch (e) {
  console.error('❌ Error: exifr not installed')
  console.error('   Run: npm install exifr')
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
 * Check image for EXIF/GPS data using sharp + exifr (fail-closed for WebP)
 * Returns: { readable, hasExif, hasGPS, tags, error }
 */
async function checkImageForExif(filePath) {
  const ext = path.extname(filePath).toLowerCase()
  
  // For WebP: FAIL CLOSED - use sharp to verify readability
  if (ext === '.webp') {
    try {
      const metadata = await sharp(filePath).metadata()
      
      // WebP must be readable by sharp (fail if corrupted/junk)
      if (!metadata || !metadata.format) {
        return {
          readable: false,
          hasExif: false,
          hasGPS: false,
          tags: {},
          error: 'WebP file unreadable or corrupted'
        }
      }
      
      // Check for metadata in WebP
      let allData = {}
      
      // Decode EXIF if present
      if (metadata.exif && Buffer.isBuffer(metadata.exif)) {
        // Strip "Exif\0\0" header if present (6 bytes)
        const exifBuffer = metadata.exif[0] === 0x45 && metadata.exif[1] === 0x78
          ? metadata.exif.slice(6)
          : metadata.exif
        
        try {
          const exifData = await exifr.parse(exifBuffer) || {}
          allData = { ...allData, ...exifData }
        } catch (e) {
          // EXIF present but unreadable = fail closed
          return {
            readable: false,
            hasExif: false,
            hasGPS: false,
            tags: {},
            error: 'WebP EXIF unreadable: ' + e.message
          }
        }
      }
      
      // Decode XMP if present
      if (metadata.xmp && Buffer.isBuffer(metadata.xmp)) {
        try {
          const xmpData = await exifr.parse(metadata.xmp) || {}
          allData = { ...allData, ...xmpData }
        } catch (e) {
          // XMP present but unreadable = fail closed
          return {
            readable: false,
            hasExif: false,
            hasGPS: false,
            tags: {},
            error: 'WebP XMP unreadable: ' + e.message
          }
        }
      }
      
      // Decode IPTC if present
      if (metadata.iptc && Buffer.isBuffer(metadata.iptc)) {
        try {
          const iptcData = await exifr.parse(metadata.iptc) || {}
          allData = { ...allData, ...iptcData }
        } catch (e) {
          // IPTC present but unreadable = fail closed
          return {
            readable: false,
            hasExif: false,
            hasGPS: false,
            tags: {},
            error: 'WebP IPTC unreadable: ' + e.message
          }
        }
      }
      
      // Check for GPS data
      const hasGPS = allData && (
        allData.latitude !== undefined ||
        allData.longitude !== undefined ||
        allData.GPSLatitude !== undefined ||
        allData.GPSLongitude !== undefined ||
        allData.GPSAltitude !== undefined
      )
      
      // Check for sensitive EXIF data (excluding benign JFIF fields)
      const hasSensitiveExif = allData && Object.keys(allData).length > 0 && !isBenignMetadata(allData)
      
      return {
        readable: true,
        hasExif: hasSensitiveExif,
        hasGPS,
        tags: allData || {}
      }
    } catch (e) {
      // FAIL CLOSED: unreadable WebP files are violations
      return {
        readable: false,
        hasExif: false,
        hasGPS: false,
        tags: {},
        error: e.message
      }
    }
  }
  
  // For JPEG/PNG/HEIC: use exifr directly (already works)
  try {
    const data = await exifr.parse(filePath, {
      tiff: true,
      exif: true,
      gps: true,
      xmp: true,
      iptc: true,
      icc: false,
      jfif: true
    }) || {}

    // Check for GPS data
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
