'use client'

import { useState } from 'react'
import MetricsPreview from '@/components/MetricsPreview'
import { useDataCache } from '@/contexts/DataCacheContext'

export default function Summary() {
  const { baseWeek, periods } = useDataCache()
  const [metrics, setMetrics] = useState(null)

  return (
    <div className="space-y-8">
      <div className="bg-white rounded-lg shadow p-6">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">Summary Metrics</h2>
        {periods ? (
          <MetricsPreview 
            periods={periods}
            baseWeek={baseWeek}
            onMetricsChange={setMetrics}
          />
        ) : (
          <div className="text-sm text-gray-600">No periods loaded. Please refresh data.</div>
        )}
      </div>
    </div>
  )
}

