'use client'

import { useState, useEffect } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import FileUpload from '@/components/FileUpload'
import FileMetadata from '@/components/FileMetadata'
import PeriodSelector from '@/components/PeriodSelector'
import { Separator } from '@/components/ui/separator'
import { useDataCache } from '@/contexts/DataCacheContext'
import { Loader2, RefreshCw, CheckCircle2, XCircle } from 'lucide-react'

export default function Settings() {
  const { refreshData, loading, loadingProgress, baseWeek, setBaseWeek } = useDataCache()
  const [selectedWeek, setSelectedWeek] = useState(baseWeek)
  const [periods, setPeriods] = useState(null)
  const [metadata, setMetadata] = useState<any>(null)
  const [dimensions, setDimensions] = useState<any>(null)
  
  // Sync selectedWeek with baseWeek from context
  useEffect(() => {
    setSelectedWeek(baseWeek)
  }, [baseWeek])

  const loadMetadata = async (clearCache = false) => {
    // Check cache first
    const cacheKey = `file_metadata_${selectedWeek}`
    
    if (clearCache) {
      localStorage.removeItem(cacheKey)
    } else {
      const cached = localStorage.getItem(cacheKey)
      
      if (cached) {
        try {
          const parsed = JSON.parse(cached)
          const cacheAge = Date.now() - parsed.timestamp
          // Cache for 5 minutes (reduced from 1 hour for more frequent updates)
          if (cacheAge < 5 * 60 * 1000) {
            setMetadata(parsed.data)
            return
          }
        } catch (err) {
          console.warn('Failed to load cached metadata:', err)
        }
      }
    }
    
    try {
      const response = await fetch(`http://localhost:8000/api/file-metadata?week=${selectedWeek}`)
      
      if (!response.ok) {
        throw new Error(`Failed to fetch metadata: ${response.statusText}`)
      }
      
      const data = await response.json()
      
      // Check if we got valid data
      if (data && typeof data === 'object') {
        setMetadata(data)
        // Save to cache
        localStorage.setItem(cacheKey, JSON.stringify({
          data,
          timestamp: Date.now()
        }))
      } else {
        console.error('Invalid metadata response:', data)
        setMetadata({}) // Set empty object to show "No file uploaded yet"
      }
    } catch (error) {
      console.error('Failed to load metadata:', error)
      // Don't set metadata to null, leave it as undefined so we show loading state
      // Or set it to empty object to show "No file uploaded yet"
      setMetadata({})
    }
  }

  const loadDimensions = async () => {
    try {
      const response = await fetch(`http://localhost:8000/api/file-dimensions?week=${selectedWeek}`)
      if (!response.ok) {
        console.warn(`Failed to fetch dimensions: ${response.statusText}`)
        setDimensions({})
        return
      }
      const data = await response.json()
      setDimensions(data)
    } catch (error) {
      console.warn('Failed to load dimensions:', error)
      setDimensions({})
    }
  }

  // Remove auto-load - metadata should only load when user clicks "Reload Metadata"
  // Load cached metadata on mount if available
  useEffect(() => {
    const cacheKey = `file_metadata_${selectedWeek}`
    const cached = localStorage.getItem(cacheKey)
    
    if (cached) {
      try {
        const parsed = JSON.parse(cached)
        const cacheAge = Date.now() - parsed.timestamp
        // Cache for 30 minutes
        if (cacheAge < 30 * 60 * 1000) {
          setMetadata(parsed.data)
        } else {
          setMetadata({}) // Show empty state
        }
      } catch (err) {
        console.warn('Failed to load cached metadata:', err)
        setMetadata({})
      }
    } else {
      setMetadata({}) // Show empty state
    }
  }, [selectedWeek])

  const fileTypes = [
    { type: 'qlik', label: 'Qlik Sales Data', formats: '.xlsx,.csv' },
    { type: 'dema_spend', label: 'DEMA Marketing Spend', formats: '.csv' },
    { type: 'dema_gm2', label: 'DEMA GM2 Data', formats: '.csv' },
    { type: 'shopify', label: 'Shopify Sessions Data', formats: '.csv' }
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
              onPeriodsChange={setPeriods}
            />
          </div>

          <Separator />

          <div>
            <h3 className="text-sm font-medium mb-3">Data Management</h3>
            <div className="flex items-center gap-4">
              <Button
                onClick={async () => {
                  await refreshData()
                  loadDimensions()
                }}
                disabled={loading}
                variant="outline"
                className="flex items-center gap-2"
              >
                {loading ? (
                  <Loader2 className="h-4 w-4 animate-spin" />
                ) : (
                  <RefreshCw className="h-4 w-4" />
                )}
                {loading ? 'Refreshing...' : 'Refresh All Data'}
              </Button>
              <Button
                onClick={() => {
                  loadMetadata(true)
                  loadDimensions()
                }}
                variant="ghost"
                className="flex items-center gap-2"
              >
                <RefreshCw className="h-4 w-4" />
                Reload Metadata
              </Button>
              {loading && loadingProgress && (
                <div className="text-sm text-gray-600">
                  {loadingProgress.message} ({loadingProgress.percentage}%)
                </div>
              )}
            </div>
            <p className="text-xs text-gray-500 mt-2">
              Manually trigger data loading process. This will refresh all cached data.
            </p>
          </div>

          <Separator />

          <div className="space-y-6">
            <h3 className="text-sm font-medium">Upload Files for Week {selectedWeek}</h3>
            
            {fileTypes.map((ft) => (
              <div key={ft.type} className="space-y-2">
                <FileUpload
                  fileType={ft.type}
                  fileTypeLabel={ft.label}
                  acceptedFormats={ft.formats}
                  currentWeek={selectedWeek}
                  onUploadSuccess={async () => {
                    await loadMetadata(true)
                    await loadDimensions()
                  }}
                />
                
                {metadata === null ? (
                  <div className="text-sm text-gray-500 italic flex items-center gap-2">
                    <Loader2 className="h-4 w-4 animate-spin" />
                    Loading...
                  </div>
                ) : metadata && metadata[ft.type] ? (
                  <FileMetadata
                    filename={metadata[ft.type].filename}
                    firstDate={metadata[ft.type].first_date}
                    lastDate={metadata[ft.type].last_date}
                    uploadedAt={metadata[ft.type].uploaded_at}
                    rowCount={metadata[ft.type].row_count}
                  />
                ) : (
                  <div className="text-sm text-gray-500 italic">
                    No file uploaded yet
                  </div>
                )}
                
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
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  )
}

