#!/usr/bin/env tsx

import puppeteer from 'puppeteer'
import { PDFDocument } from 'pdf-lib'
import * as path from 'path'
import * as fs from 'fs'
import { fileURLToPath } from 'url'

const BASE_URL = process.env.NEXT_PUBLIC_FRONTEND_URL || process.env.FRONTEND_URL || 'http://localhost:3000'

// Get the project root directory (one level up from frontend/scripts/)
const __filename = fileURLToPath(import.meta.url)
const __dirname = path.dirname(__filename)
const frontendDir = path.resolve(__dirname, '..')
const projectRoot = path.resolve(frontendDir, '..')
const OUTPUT_DIR = path.join(projectRoot, 'reports')

interface PageConfig {
  name: string
  url: string
  waitForSelector?: string
}

const PAGES: PageConfig[] = [
  {
    name: 'Summary',
    url: '/reports/weekly',
    waitForSelector: 'table tbody tr'
  },
  {
    name: 'Top Markets',
    url: '/reports/weekly',
    waitForSelector: 'table tbody tr'
  }
]

async function waitForPageLoad(page: puppeteer.Page, pageConfig: PageConfig, week: string): Promise<void> {
  console.log(`📄 Loading ${pageConfig.name} page...`)
  
  // Wait for fonts to load
  await page.evaluate(() => document.fonts.ready)

  // Wait for "Loading Dashboard Data" progress indicator to disappear
  try {
    await page.waitForFunction(
      () => {
        const loadingText = Array.from(document.querySelectorAll('*')).find(
          (el) => {
            const text = el.textContent || ''
            return text.includes('Loading Dashboard Data')
          }
        )
        
        if (loadingText) {
          let container = loadingText as HTMLElement
          while (container && container !== document.body) {
            const style = window.getComputedStyle(container)
            if (style.display === 'none' || style.visibility === 'hidden' || style.opacity === '0') {
              return true
            }
            if (container.classList.toString().includes('card') || container.classList.toString().includes('Card')) {
              const containerStyle = window.getComputedStyle(container)
              if (containerStyle.display === 'none' || containerStyle.visibility === 'hidden') {
                return true
              }
              return false
            }
            container = container.parentElement as HTMLElement
          }
          return false
        }
        
        const allText = document.body.textContent || ''
        if (allText.includes('Step') && allText.includes('of') && allText.includes('complete')) {
          return false
        }
        
        const table = document.querySelector('table')
        if (table) {
          const tableStyle = window.getComputedStyle(table)
          if (tableStyle.display !== 'none' && tableStyle.visibility !== 'hidden') {
            return true
          }
        }
        
        return true
      },
      { timeout: 120000 }
    )
  } catch (e) {
    console.warn(`⚠️ Loading progress check failed for ${pageConfig.name}, continuing...`)
  }
  
  // Wait for loading spinner to disappear
  try {
    await page.waitForFunction(
      () => {
        const spinner = document.querySelector('.animate-spin, [class*="animate-spin"]')
        if (spinner) {
          const style = window.getComputedStyle(spinner)
          return style.display === 'none' || style.visibility === 'hidden' || style.opacity === '0'
        }
        return true
      },
      { timeout: 60000 }
    )
  } catch (e) {
    console.warn(`⚠️ Spinner check failed for ${pageConfig.name}, continuing...`)
  }

  // Wait for table or charts to be populated with data
  if (pageConfig.waitForSelector) {
    try {
      await page.waitForFunction(
        () => {
          // For tables, check if table has data
          if (pageConfig.waitForSelector?.includes('table')) {
            const table = document.querySelector('table')
            if (!table) return false
            
            const rows = table.querySelectorAll('tbody tr')
            if (rows.length === 0) return false
            
            for (const row of Array.from(rows)) {
              const cells = row.querySelectorAll('td')
              if (cells.length > 0) {
                const firstDataCell = cells[1]
                if (firstDataCell && firstDataCell.textContent) {
                  const text = firstDataCell.textContent.trim()
                  if (text && text !== 'Loading metrics...' && text !== '-' && text !== '0' && !text.includes('Loading')) {
                    return true
                  }
                }
              }
            }
            
            return false
          }
          
          // For charts/cards, check if cards are visible and have content
          if (pageConfig.waitForSelector?.includes('card') || pageConfig.waitForSelector?.includes('Card')) {
            const cards = document.querySelectorAll('.card, [class*="Card"]')
            if (cards.length === 0) return false
            
            // Check if at least one card has chart content (svg elements)
            for (const card of Array.from(cards)) {
              const svg = card.querySelector('svg')
              if (svg && svg.children.length > 0) {
                return true
              }
            }
            
            // If no SVG found, check if cards have text content (not just loading)
            const hasContent = Array.from(cards).some(card => {
              const text = card.textContent || ''
              return text && !text.includes('Loading') && !text.includes('Processing')
            })
            
            return hasContent
          }
          
          return true
        },
        { timeout: 90000 }
      )
      console.log(`   ✅ ${pageConfig.name} content populated`)
    } catch (e) {
      console.warn(`   ⚠️ Content not populated for ${pageConfig.name}, continuing anyway...`)
    }
  }

  // Additional wait to ensure all data is rendered
  await new Promise(resolve => setTimeout(resolve, 2000))
}

async function makeReportPdf(week: string) {
  if (!week || !/^\d{4}-\d{2}$/.test(week)) {
    throw new Error('Invalid week format. Expected format: YYYY-WW (e.g., 2025-42)')
  }

  console.log(`\n🚀 Generating PDF for week: ${week}`)
  console.log(`📁 Output directory: ${OUTPUT_DIR}`)

  // Ensure output directory exists
  if (!fs.existsSync(OUTPUT_DIR)) {
    fs.mkdirSync(OUTPUT_DIR, { recursive: true })
  }

  const weekDir = path.join(OUTPUT_DIR, week)
  if (!fs.existsSync(weekDir)) {
    fs.mkdirSync(weekDir, { recursive: true })
  }

  const outputPath = path.join(weekDir, 'weekly-report.pdf')
  const tempDir = path.join(weekDir, 'temp-pages')
  if (!fs.existsSync(tempDir)) {
    fs.mkdirSync(tempDir, { recursive: true })
  }

  const browser = await puppeteer.launch({
    headless: true,
    args: ['--no-sandbox', '--disable-setuid-sandbox'],
    timeout: 180000, // 3 minutes for browser launch
  })

  try {
    const pdfPages: Buffer[] = []
    const pageConfigs: PageConfig[] = [
      {
        name: 'Summary',
        url: `${BASE_URL}/reports/weekly/${week}?pdf=1`,
        waitForSelector: 'table tbody tr'
      },
      {
        name: 'Top Markets',
        url: `${BASE_URL}/reports/weekly/${week}/top-markets?pdf=1`,
        waitForSelector: 'table tbody tr'
      },
      {
        name: 'Online KPIs',
        url: `${BASE_URL}/reports/weekly/${week}/online-kpis?pdf=1`,
        waitForSelector: '.card, [class*="Card"]'
      }
    ]

    // Generate each page using a separate page instance to avoid detached frame errors
    for (let i = 0; i < pageConfigs.length; i++) {
      const pageConfig = pageConfigs[i]
      const pageNum = i + 1
      const totalPages = pageConfigs.length
      
      console.log(`\n📄 [${pageNum}/${totalPages}] Generating ${pageConfig.name} page...`)
      console.log(`   URL: ${pageConfig.url}`)

      // Create a new page for each PDF to avoid detached frame errors
      const page = await browser.newPage()
      page.setDefaultNavigationTimeout(180000) // 3 minutes for navigation
      page.setDefaultTimeout(180000) // 3 minutes for all operations

      try {
        try {
          await page.goto(pageConfig.url, {
            waitUntil: 'domcontentloaded',
            timeout: 180000, // 3 minutes for pages that take longer to load
          })
        } catch (error: any) {
          if (error.name === 'TimeoutError') {
            console.warn(`   ⚠️ Navigation timeout for ${pageConfig.name}, but continuing...`)
            // Try to continue anyway - the page might have partially loaded
          } else {
            throw error
          }
        }

        console.log(`   ✅ Page loaded, waiting for content...`)
        console.log(`   📄 Loading ${pageConfig.name} page...`)

        // Wait for main content
        try {
          await page.waitForSelector(pageConfig.waitForSelector || 'table, [role="table"], .card, main', {
            timeout: 120000, // 2 minutes
          })
        } catch (e) {
          console.warn(`   ⚠️ Main content selector not found, continuing...`)
        }

        // Wait for page to fully load
        try {
          await waitForPageLoad(page, pageConfig, week)
        } catch (e) {
          console.warn(`   ⚠️ Error waiting for page load: ${e}, continuing anyway...`)
        }

        console.log(`   ✅ ${pageConfig.name} content loaded`)
        console.log(`   📄 Generating PDF for ${pageConfig.name}...`)
        
        // Generate PDF for this page
        // Set preferCSSPageSize to false to prevent CSS page-break rules from creating empty pages
        const pagePdf = await page.pdf({
          format: 'A4',
          landscape: true,
          printBackground: true,
          preferCSSPageSize: false, // Disable CSS page size to avoid empty pages
          margin: {
            top: '12mm',
            right: '12mm',
            bottom: '14mm',
            left: '12mm',
          },
          scale: 1,
        })

        pdfPages.push(Buffer.from(pagePdf))
        console.log(`   ✅ [${pageNum}/${totalPages}] ${pageConfig.name} page generated (${pagePdf.length} bytes)`)
      } finally {
        // Always close the page after generating PDF to avoid detached frame errors
        await page.close()
      }
    }

    // Combine all pages into one PDF, taking only the first page from each PDF
    console.log(`\n🔗 Combining ${pdfPages.length} pages into final PDF...`)
    const mergedPdf = await PDFDocument.create()
    
    for (let i = 0; i < pdfPages.length; i++) {
      const pageConfig = pageConfigs[i]
      console.log(`   Adding ${pageConfig.name} page...`)
      const pdfDoc = await PDFDocument.load(pdfPages[i])
      const allPages = pdfDoc.getPageIndices()
      
      // Only take the first page from each PDF to avoid empty pages
      // If the content is split across multiple pages, we'll need to fix CSS instead
      const pagesToCopy = [0] // Always take only the first page
      const pages = await mergedPdf.copyPages(pdfDoc, pagesToCopy)
      pages.forEach((page) => mergedPdf.addPage(page))
      
      if (allPages.length > 1) {
        console.log(`   ⚠️ ${pageConfig.name} PDF had ${allPages.length} pages, taking only the first one`)
      }
      console.log(`   ✅ Added ${pagesToCopy.length} page(s) from ${pageConfig.name}`)
    }

    // Save merged PDF
    const mergedPdfBytes = await mergedPdf.save()
    fs.writeFileSync(outputPath, mergedPdfBytes)

    // Clean up temp directory
    try {
      fs.rmSync(tempDir, { recursive: true, force: true })
    } catch (e) {
      console.warn(`⚠️ Could not clean up temp directory: ${e}`)
    }

    // Verify file was created
    if (!fs.existsSync(outputPath)) {
      throw new Error(`PDF file was not created at ${outputPath}`)
    }

    const stats = fs.statSync(outputPath)
    console.log(`\n✅ PDF generated successfully: ${outputPath}`)
    console.log(`📊 PDF file size: ${stats.size} bytes`)
    console.log(`📄 Total pages: ${pdfPages.length}`)
    
    return outputPath
  } catch (error) {
    console.error('❌ Error during PDF generation:', error)
    throw error
  } finally {
    await browser.close()
  }
}

// Main execution
const week = process.argv[2]

if (!week) {
  console.error('Usage: tsx scripts/makeReportPdf.ts <week>')
  console.error('Example: tsx scripts/makeReportPdf.ts 2025-42')
  process.exit(1)
}

makeReportPdf(week)
  .then((outputPath) => {
    console.log(`\n✅ Success! PDF saved to: ${outputPath}`)
    process.exit(0)
  })
  .catch((error) => {
    console.error('\n❌ Error generating PDF:', error)
    process.exit(1)
  })
