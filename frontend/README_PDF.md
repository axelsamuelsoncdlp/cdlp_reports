# PDF Generation with Visual Parity

## Overview

This document describes the PDF generation system that replaces the previous screenshot-based approach with a Puppeteer-based HTML/SVG rendering system. The goal is **visual parity**: charts and tables in the generated PDF must exactly match the existing on-site components.

## Running PDF Generation

### Command Line

```bash
cd frontend
pnpm run pdf:weekly <week>
```

Example:
```bash
pnpm run pdf:weekly 2025-42
```

The PDF will be saved to `reports/<week>/weekly-report.pdf`.

### Via API

The Python API endpoint `/api/generate/weekly-reports-pdf` has been updated to use the Puppeteer script instead of screenshots. It maintains the same SSE (Server-Sent Events) progress updates for compatibility with the frontend.

## Architecture

### Components

1. **`/app/reports/weekly/[week]/page.tsx`** - Server component route that renders the summary page
2. **`usePdfMode()` hook** - Detects PDF mode from `?pdf=1` query param or `data-pdf` attribute
3. **`PdfLayout` component** - Conditionally excludes SidebarLayout when in PDF mode
4. **`MetricsPreview` component** - Reused as-is with PDF mode enhancements (tabular-nums, page breaks)
5. **`makeReportPdf.ts`** - Puppeteer script that generates PDF from the route

### Visual Parity Strategy

- **Reuse, don't restyle**: Import and render the same React components used on the site
- **Tailwind classes**: All styling comes from existing Tailwind classes and shadcn variants
- **Design tokens**: Colors, spacing, radii come from Tailwind config
- **Fonts**: Inter from Google Fonts (embedded in PDF via Puppeteer)
- **Print optimizations**: Only minimal adjustments for A4 readability:
  - Fixed chart sizes (if charts are added later)
  - Slightly larger base font-size (11-12pt) for print
  - Page-break utilities to avoid orphan rows
  - `tabular-nums` for numeric alignment

## Visual Parity Checklist

Before deploying, verify:

- [x] Same Tailwind classes used (verified in code)
- [x] Tables: same header weight, row height, borders, numeric alignment
- [x] Typography: same font family/weights; sizes scaled uniformly for print
- [x] Colors: exact tokens from Tailwind/shadcn; no ad-hoc hex codes
- [ ] PDF zoom to 200% shows crisp fonts (test after Puppeteer installation)
- [ ] No unexpected line wraps or overflow beyond margins

## Setup

1. Install dependencies:
   ```bash
   cd frontend
   pnpm install
   ```

2. Ensure Next.js dev server is running:
   ```bash
   pnpm dev
   ```

3. Run PDF generation:
   ```bash
   pnpm run pdf:weekly 2025-42
   ```

## Technical Notes

- **MetricsPreview** uses plain HTML table (not shadcn Table) - this is fine, reused as-is
- **PDF mode** detected via query param `?pdf=1` and `data-pdf` attribute
- **Puppeteer** renders HTML/SVG natively (no screenshot blur)
- **A4 landscape** format with 12mm margins
- **Font loading**: Script waits for `document.fonts.ready` before generating PDF

## Troubleshooting

### Puppeteer not found

Ensure Puppeteer is installed:
```bash
cd frontend
pnpm install puppeteer
```

### PDF generation fails

Check:
1. Next.js dev server is running on `http://localhost:3000`
2. The route `/reports/weekly/<week>?pdf=1` loads correctly in browser
3. Check backend logs for detailed error messages

### Fonts not rendering correctly

Ensure fonts are loaded before PDF generation. The script waits for `document.fonts.ready`, but if issues persist, increase the timeout in `makeReportPdf.ts`.

## Future Enhancements

- Add more pages to PDF (currently only Summary)
- Add charts with fixed-size SVG rendering
- Support for custom page sizes
- Progress indicators during PDF generation




