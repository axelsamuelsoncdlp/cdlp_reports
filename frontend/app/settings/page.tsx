'use client'

import { useState, useEffect } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import FileUpload from '@/components/FileUpload'
import FileMetadata from '@/components/FileMetadata'
import PeriodSelector from '@/components/PeriodSelector'
import { Separator } from '@/components/ui/separator'
import { Loader2 } from 'lucide-react'

export default function Settings() {
  const [selectedWeek, setSelectedWeek] = useState('2025-42')
  const [periods, setPeriods] = useState(null)
  const [metadata, setMetadata] = useState<any>(null)
  const [loading, setLoading] = useState(false)

  const loadMetadata = async () => {
    setLoading(true)
    try {
      const response = await fetch(`http://localhost:8000/api/file-metadata?week=${selectedWeek}`)
      const data = await response.json()
      setMetadata(data)
    } catch (error) {
      console.error('Failed to load metadata:', error)
    } finally {
      setLoading(false)
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

          <div className="space-y-6">
            <h3 className="text-sm font-medium">Upload Files for Week {selectedWeek}</h3>
            
            {fileTypes.map((ft) => (
              <div key={ft.type} className="space-y-2">
                <FileUpload
                  fileType={ft.type}
                  fileTypeLabel={ft.label}
                  acceptedFormats={ft.formats}
                  currentWeek={selectedWeek}
                  onUploadSuccess={loadMetadata}
                />
                
                {loading ? (
                  <div className="flex items-center gap-2 text-sm text-gray-500">
                    <Loader2 className="h-4 w-4 animate-spin" />
                    Loading status...
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
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  )
}

