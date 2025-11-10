'use client'

import { useState, useEffect, useCallback, useRef } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Switch } from '@/components/ui/switch'
import BatchFileUpload from '@/components/BatchFileUpload'
import FileMetadata from '@/components/FileMetadata'
import PeriodSelector from '@/components/PeriodSelector'
import { Separator } from '@/components/ui/separator'
import { useDataCache } from '@/contexts/DataCacheContext'
import { useChartSettings } from '@/contexts/ChartSettingsContext'
import { RefreshCw, CheckCircle2, XCircle } from 'lucide-react'

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'
const METADATA_CACHE_EXPIRY = 10 * 60 * 1000 // 10 minutes
const DIMENSIONS_CACHE_EXPIRY = 10 * 60 * 1000 // 10 minutes

export default function Settings() {
  const { refreshData, loading, loadingProgress, baseWeek, setBaseWeek } = useDataCache()
  const { animationsEnabled, setAnimationsEnabled, setIsPdfGeneration } = useChartSettings()
  const [selectedWeek, setSelectedWeek] = useState(baseWeek)
  const [periods, setPeriods] = useState<any>(null)
  const [metadata, setMetadata] = useState<any>(null)
  const [dimensions, setDimensions] = useState<any>(null)
  const [pdfGenerating, setPdfGenerating] = useState(false)
  const [pdfProgress, setPdfProgress] = useState<any>(null)
  const [loadingDimensions, setLoadingDimensions] = useState(false)
  const metadataTimeoutRef = useRef<NodeJS.Timeout | null>(null)
  const pdfDownloadedRef = useRef<boolean>(false) // Track if PDF has been downloaded to prevent duplicate downloads
  
  // Sync selectedWeek with baseWeek from context
  useEffect(() => {
    setSelectedWeek(baseWeek)
  }, [baseWeek])

  const loadMetadata = useCallback(async (clearCache = false) => {
    const cacheKey = `file_metadata_${selectedWeek}`
    
    if (clearCache) {
      localStorage.removeItem(cacheKey)
    } else {
      const cached = localStorage.getItem(cacheKey)
      if (cached) {
        try {
          const parsed = JSON.parse(cached)
          const cacheAge = Date.now() - parsed.timestamp
          if (cacheAge < METADATA_CACHE_EXPIRY) {
            setMetadata(parsed.data)
            return
          }
        } catch (err) {
          console.warn('Failed to load cached metadata:', err)
        }
      }
    }
    
    try {
      const response = await fetch(`${API_BASE_URL}/api/file-metadata?week=${selectedWeek}`)
      
      if (!response.ok) {
        throw new Error(`Failed to fetch metadata: ${response.statusText}`)
      }
      
      const data = await response.json()
      
      if (data && typeof data === 'object') {
        setMetadata(data)
        localStorage.setItem(cacheKey, JSON.stringify({
          data,
          timestamp: Date.now()
        }))
      } else {
        console.error('Invalid metadata response:', data)
        setMetadata({})
      }
    } catch (error) {
      console.error('Failed to load metadata:', error)
      setMetadata({})
    }
  }, [selectedWeek])

  const loadDimensions = useCallback(async (clearCache = false) => {
    setLoadingDimensions(true)
    const cacheKey = `file_dimensions_${selectedWeek}`
    
    if (clearCache) {
      localStorage.removeItem(cacheKey)
    } else {
      const cached = localStorage.getItem(cacheKey)
      if (cached) {
        try {
          const parsed = JSON.parse(cached)
          const cacheAge = Date.now() - parsed.timestamp
          if (cacheAge < DIMENSIONS_CACHE_EXPIRY) {
            setDimensions(parsed.data)
            setLoadingDimensions(false)
            return
          }
        } catch (err) {
          console.warn('Failed to load cached dimensions:', err)
        }
      }
    }
    
    try {
      const response = await fetch(`${API_BASE_URL}/api/file-dimensions?week=${selectedWeek}`)
      if (!response.ok) {
        console.warn(`Failed to fetch dimensions: ${response.statusText}`)
        setDimensions({})
        return
      }
      const data = await response.json()
      setDimensions(data)
      localStorage.setItem(cacheKey, JSON.stringify({
        data,
        timestamp: Date.now()
      }))
    } catch (error) {
      console.warn('Failed to load dimensions:', error)
      setDimensions({})
    } finally {
      setLoadingDimensions(false)
    }
  }, [selectedWeek])

  // Debounced metadata loading when week changes
  useEffect(() => {
    // Clear any pending timeout
    if (metadataTimeoutRef.current) {
      clearTimeout(metadataTimeoutRef.current)
    }
    
    // Debounce metadata loading by 300ms to prevent rapid API calls
    metadataTimeoutRef.current = setTimeout(() => {
      loadMetadata(false)
    }, 300)
    
    return () => {
      if (metadataTimeoutRef.current) {
        clearTimeout(metadataTimeoutRef.current)
      }
    }
  }, [selectedWeek, loadMetadata])

  const fileTypes = [
    { type: 'qlik', label: 'Qlik Sales Data', formats: '.xlsx,.csv' },
    { type: 'dema_spend', label: 'DEMA Marketing Spend', formats: '.csv' },
    { type: 'dema_gm2', label: 'DEMA GM2 Data', formats: '.csv' },
    { type: 'shopify', label: 'Shopify Sessions Data', formats: '.csv' },
    { type: 'budget', label: 'Budget Data', formats: '.csv' }
  ]

  return (
    <div className="space-y-8">
      <Card>
        <CardHeader>
          <CardTitle>Data File Management</CardTitle>
          <CardDescription>
            Upload weekly data files and view their status
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-6">
          {/* Weekly Reports PDF */}
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <div>
                <h3 className="text-sm font-medium mb-1">Export Weekly Reports</h3>
                <p className="text-xs text-gray-500">Generate a single PDF with all Weekly Reports pages for the selected week.</p>
              </div>
              <Button
                onClick={async (e) => {
                  e.preventDefault() // Prevent any default behavior
                  e.stopPropagation() // Stop event bubbling
                  
                  // Reset download flag
                  pdfDownloadedRef.current = false
                  
                  setPdfGenerating(true)
                  setIsPdfGeneration(true) // Disable animations during PDF generation
                  // Don't set initial progress - let backend send it
                  setPdfProgress({
                    step: 'starting',
                    stepNumber: 1,
                    totalSteps: 7, // Will be updated by backend
                    message: 'Initializing PDF generation...',
                    currentPage: null,
                    percentage: 0
                  })
                  
                  try {
                    const { generateWeeklyReportsPDF } = await import('@/lib/api')
                    const periodsToInclude = ['actual','last_week','last_year']
                    const res = await generateWeeklyReportsPDF(
                      selectedWeek, 
                      periodsToInclude,
                      (progress) => {
                        // Update progress with data from backend
                        setPdfProgress(progress)
                        
                        // If we got a result, download the PDF (only once)
                        if (progress.result && !pdfDownloadedRef.current) {
                          pdfDownloadedRef.current = true // Mark as downloaded
                          const url = `${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}${progress.result.download_url}`
                          // Use fetch to download PDF instead of window.open to prevent page refresh
                          fetch(url)
                            .then(response => response.blob())
                            .then(blob => {
                              const downloadUrl = window.URL.createObjectURL(blob)
                              const a = document.createElement('a')
                              a.href = downloadUrl
                              a.download = progress.result.download_url.split('/').pop() || 'weekly_reports.pdf'
                              document.body.appendChild(a)
                              a.click()
                              document.body.removeChild(a)
                              window.URL.revokeObjectURL(downloadUrl)
                            })
                            .catch(err => {
                              console.error('Failed to download PDF:', err)
                              alert('Failed to download PDF. Please try again.')
                            })
                          setPdfGenerating(false)
                          setIsPdfGeneration(false) // Re-enable animations after PDF generation
                          setPdfProgress(null)
                        }
                        
                        // If we got an error, show it
                        if (progress.error) {
                          alert(`Failed to generate PDF: ${progress.error}`)
                          setPdfGenerating(false)
                          setIsPdfGeneration(false) // Re-enable animations after PDF generation error
                          setPdfProgress(null)
                        }
                      }
                    )
                    
                    // NOTE: We don't need to download here because SSE callback already handles it
                    // Only download here if SSE didn't trigger (shouldn't happen, but safety check)
                    if (res && !pdfDownloadedRef.current) {
                      pdfDownloadedRef.current = true // Mark as downloaded
                      const url = `${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}${res.download_url}`
                      // Use fetch to download PDF instead of window.open to prevent page refresh
                      fetch(url)
                        .then(response => response.blob())
                        .then(blob => {
                          const downloadUrl = window.URL.createObjectURL(blob)
                          const a = document.createElement('a')
                          a.href = downloadUrl
                          a.download = res.download_url.split('/').pop() || 'weekly_reports.pdf'
                          document.body.appendChild(a)
                          a.click()
                          document.body.removeChild(a)
                          window.URL.revokeObjectURL(downloadUrl)
                        })
                        .catch(err => {
                          console.error('Failed to download PDF:', err)
                          alert('Failed to download PDF. Please try again.')
                        })
                      setPdfGenerating(false)
                      setIsPdfGeneration(false) // Re-enable animations after PDF generation
                      setPdfProgress(null)
                    }
                  } catch (e: any) {
                    console.error('Failed to generate Weekly Reports PDF', e)
                    alert(`Failed to generate PDF: ${e.message || 'Please try again.'}`)
                    setPdfGenerating(false)
                    setIsPdfGeneration(false) // Re-enable animations after PDF generation error
                    setPdfProgress(null)
                    pdfDownloadedRef.current = false // Reset flag on error
                  }
                }}
                variant="default"
                disabled={pdfGenerating}
              >
                {pdfGenerating ? 'Generating PDF...' : 'Generate Weekly Reports PDF'}
              </Button>
            </div>
            
            {/* PDF Generation Progress */}
            {pdfGenerating && pdfProgress && (
              <div className="space-y-3 p-4 bg-gray-50 rounded-lg border border-gray-200">
                <div className="flex items-center justify-between">
                  <div className="flex-1">
                    <div className="flex items-center gap-2 mb-1">
                      <div className="h-2 w-2 bg-blue-600 rounded-full animate-pulse"></div>
                      <span className="font-semibold text-gray-900 text-sm">Generating PDF</span>
                    </div>
                    <p className="text-sm text-gray-700 mt-1">{pdfProgress.message}</p>
                    {pdfProgress.currentPage && (
                      <div className="text-xs text-gray-600 mt-1 flex items-center gap-1">
                        <span>📄</span>
                        <span className="font-medium">{pdfProgress.currentPage}</span>
                      </div>
                    )}
                  </div>
                  <div className="text-right">
                    <div className="text-lg font-bold text-blue-600">{pdfProgress.percentage}%</div>
                    <div className="text-xs text-gray-500">
                      Step {pdfProgress.stepNumber}/{pdfProgress.totalSteps}
                    </div>
                  </div>
                </div>
                
                {/* Progress Bar */}
                <div className="w-full bg-gray-200 rounded-full h-3 overflow-hidden">
                  <div 
                    className="bg-gradient-to-r from-blue-500 to-blue-600 h-3 rounded-full transition-all duration-500 ease-out"
                    style={{ width: `${pdfProgress.percentage}%` }}
                  />
                </div>
                
                {/* Step Info */}
                <div className="flex items-center justify-between text-xs text-gray-500">
                  <span>
                    {pdfProgress.step === 'starting' && 'Preparing...'}
                    {pdfProgress.step === 'initializing' && 'Initializing Puppeteer...'}
                    {pdfProgress.step === 'loading' && 'Loading page content...'}
                    {pdfProgress.step === 'waiting' && 'Waiting for data to load...'}
                    {pdfProgress.step === 'generating' && pdfProgress.currentPage 
                      ? `Generating ${pdfProgress.currentPage} page...`
                      : 'Generating PDF pages...'}
                    {pdfProgress.step === 'combining' && 'Combining pages...'}
                    {pdfProgress.step === 'complete' && '✅ PDF generation complete!'}
                    {pdfProgress.step === 'error' && '❌ Error occurred'}
                    {!pdfProgress.step && 'Processing...'}
                  </span>
                  {pdfProgress.step !== 'complete' && pdfProgress.step !== 'error' && (
                    <span className="text-gray-400">
                      {pdfProgress.stepNumber < pdfProgress.totalSteps 
                        ? `~${Math.max(1, Math.round((pdfProgress.totalSteps - pdfProgress.stepNumber) * 0.3))} min remaining`
                        : 'Almost done...'}
                    </span>
                  )}
                </div>
              </div>
            )}
          </div>
          <Separator />
          
          {/* Chart Settings */}
          <div>
            <h3 className="text-sm font-medium mb-3">Chart Settings</h3>
            <div className="flex items-center justify-between py-2">
              <div className="flex-1">
                <div className="text-sm font-medium">Enable Chart Animations</div>
                <p className="text-xs text-gray-500 mt-1">
                  Chart animations are automatically disabled during PDF generation
                </p>
              </div>
              <Switch
                checked={animationsEnabled}
                onCheckedChange={setAnimationsEnabled}
              />
            </div>
          </div>

          <Separator />
          
          <div>
            <h3 className="text-sm font-medium mb-3">Select Week</h3>
            <PeriodSelector 
              selectedWeek={selectedWeek}
              onWeekChange={(week) => {
                setSelectedWeek(week)
                // Update the global baseWeek in DataCacheContext
                setBaseWeek(week)
                // Save the selected week to localStorage
                localStorage.setItem('selected_week', week)
              }}
              onPeriodsChange={(p) => setPeriods(p as any)}
            />
          </div>

          <Separator />

          <div>
            <h3 className="text-sm font-medium mb-3">Data Management</h3>
            <div className="flex items-center gap-4">
              <Button
                onClick={async () => {
                  await loadMetadata(true)
                }}
                variant="ghost"
                className="flex items-center gap-2"
              >
                <RefreshCw className="h-4 w-4" />
                Reload Metadata
              </Button>
              <Button
                onClick={async () => {
                  await loadDimensions(true)
                }}
                variant="ghost"
                className="flex items-center gap-2"
                disabled={loadingDimensions}
              >
                <RefreshCw className={`h-4 w-4 ${loadingDimensions ? 'animate-spin' : ''}`} />
                {loadingDimensions ? 'Loading Dimensions...' : 'Check Dimensions'}
              </Button>
            </div>
            <p className="text-xs text-gray-500 mt-2">
              Reload file metadata to check current file status. Use "Check Dimensions" to validate file structure. Data refresh happens automatically after file upload.
            </p>
          </div>

          <Separator />

          <div className="space-y-6">
            <h3 className="text-sm font-medium">Upload Files for Week {selectedWeek}</h3>
            
            <BatchFileUpload
              fileTypes={fileTypes}
              currentWeek={selectedWeek}
              onUploadComplete={async () => {
                await loadMetadata(true)
                // Don't auto-load dimensions - user can click button if needed
              }}
              refreshData={async () => {
                await refreshData()
                // Don't auto-load dimensions - user can click button if needed
              }}
              loading={loading}
              loadingProgress={loadingProgress}
            />

            {/* File Metadata Display */}
            <div className="space-y-4 mt-6">
              <h4 className="text-sm font-medium">Current Files</h4>
              {metadata === null ? (
                <div className="text-sm text-gray-500 italic">
                  Loading file status...
                </div>
              ) : (
                <div className="space-y-3">
                  {fileTypes.map((ft) => (
                    <div key={ft.type} className="space-y-2">
                      <div className="text-sm font-medium text-gray-700">{ft.label}</div>
                      {metadata && metadata[ft.type] ? (
                        <>
                          <FileMetadata
                            filename={metadata[ft.type].filename}
                            firstDate={metadata[ft.type].first_date}
                            lastDate={metadata[ft.type].last_date}
                            uploadedAt={metadata[ft.type].uploaded_at}
                            rowCount={metadata[ft.type].row_count}
                          />
                          {/* Dimension validation status */}
                          {dimensions && dimensions[ft.type] && (
                            <div className="flex items-center gap-2 text-sm">
                              {dimensions[ft.type].has_country === true ? (
                                <div className="flex items-center gap-1 text-green-600">
                                  <CheckCircle2 className="h-4 w-4" />
                                  <span>Country dimension detected</span>
                                </div>
                              ) : dimensions[ft.type].has_country === false ? (
                                <div className="flex items-center gap-1 text-red-600">
                                  <XCircle className="h-4 w-4" />
                                  <span>Country dimension missing</span>
                                </div>
                              ) : null}
                            </div>
                          )}
                        </>
                      ) : (
                        <div className="text-sm text-gray-500 italic">
                          No file uploaded yet
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}

