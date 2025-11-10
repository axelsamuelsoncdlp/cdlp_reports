'use client'

import { ReactNode, useEffect } from 'react'
import { useSearchParams } from 'next/navigation'

interface PdfLayoutProps {
  children: ReactNode
}

/**
 * Layout component that excludes SidebarLayout when in PDF mode
 * Sets data-pdf attribute on root element for CSS targeting
 */
export default function PdfLayout({ children }: PdfLayoutProps) {
  const searchParams = useSearchParams()
  const pdfParam = searchParams?.get('pdf')
  const isPdfMode = pdfParam === '1' || pdfParam === 'true'

  useEffect(() => {
    // Set data-pdf attribute on html element when in PDF mode
    // Do this synchronously before React renders to ensure CSS applies
    if (typeof document !== 'undefined') {
      if (isPdfMode) {
        document.documentElement.setAttribute('data-pdf', 'true')
      } else {
        document.documentElement.removeAttribute('data-pdf')
      }
    }
  }, [isPdfMode])

  // In PDF mode, render without sidebar layout
  if (isPdfMode) {
    return (
      <div className="min-h-screen bg-white">
        <main className="p-6">
          {children}
        </main>
      </div>
    )
  }

  // Normal mode - render children as-is (will be wrapped by SidebarLayout from root layout)
  return <>{children}</>
}

