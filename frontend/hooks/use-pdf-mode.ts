'use client'

import { useSearchParams } from 'next/navigation'
import { useEffect, useState } from 'react'

/**
 * Hook to detect PDF mode from query param and data-pdf attribute
 * @returns boolean indicating if PDF mode is active
 */
export function usePdfMode(): boolean {
  const searchParams = useSearchParams()
  const [isPdfMode, setIsPdfMode] = useState(false)

  useEffect(() => {
    // Check query param ?pdf=1
    const pdfParam = searchParams?.get('pdf')
    const hasPdfParam = pdfParam === '1' || pdfParam === 'true'

    // Check for parent data-pdf attribute
    const checkDataPdf = () => {
      if (typeof document === 'undefined') return false
      let element: HTMLElement | null = document.documentElement
      while (element) {
        if (element.getAttribute('data-pdf') === 'true') {
          return true
        }
        element = element.parentElement
      }
      return false
    }

    const hasDataPdf = checkDataPdf()
    setIsPdfMode(hasPdfParam || hasDataPdf)
  }, [searchParams])

  return isPdfMode
}




