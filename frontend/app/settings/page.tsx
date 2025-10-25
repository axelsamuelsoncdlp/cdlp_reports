'use client'

import { useState, useEffect } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import FileUpload from '@/components/FileUpload'
import FileMetadata from '@/components/FileMetadata'
import PeriodSelector from '@/components/PeriodSelector'
import { Separator } from '@/components/ui/separator'
import { useDataCache } from '@/contexts/DataCacheContext'
import { Loader2, RefreshCw } from 'lucide-react'

export default function Settings() {
  const [selectedWeek, setSelectedWeek] = useState('2025-42')
  const [periods, setPeriods] = useState(null)
  const [metadata, setMetadata] = useState<any>(null)
  const { refreshData, loading, loadingProgress } = useDataCache()

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
          // Cache for 1 hour
          if (cacheAge < 60 * 60 * 1000) {
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
      const data = await response.json()
      setMetadata(data)
      // Save to cache
      localStorage.setItem(cacheKey, JSON.stringify({
        data,
        timestamp: Date.now()
      }))
    } catch (error) {
      console.error('Failed to load metadata:', error)
    }
  }

  useEffect(() => {
    loadMetadata()
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
              onWeekChange={setSelectedWeek}
              onPeriodsChange={setPeriods}
            />
          </div>

          <Separator />

          <div>
            <h3 className="text-sm font-medium mb-3">Data Management</h3>
            <div className="flex items-center gap-4">
              <Button
                onClick={refreshData}
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
                  onUploadSuccess={() => loadMetadata(true)}
                />
                
                {metadata && metadata[ft.type] ? (
                  <FileMetadata
                    filename={metadata[ft.type].filename}
                    firstDate={metadata[ft.type].first_date}
                    lastDate={metadata[ft.type].last_date}
                    uploadedAt={metadata[ft.type].uploaded_at}
                    rowCount={metadata[ft.type].row_count}
                  />
                ) : metadata ? (
                  <div className="text-sm text-gray-500 italic">
                    No file uploaded yet
                  </div>
                ) : null}
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  )
}

