'use client'

import { useState, useEffect } from 'react'
import MetricsPreview from '@/components/MetricsPreview'
import { getPeriods } from '@/lib/api'

export default function Summary() {
  const [selectedWeek, setSelectedWeek] = useState('2025-42')
  const [periods, setPeriods] = useState(null)
  const [metrics, setMetrics] = useState(null)

  // Load periods on mount
  useEffect(() => {
    const loadPeriods = async () => {
      try {
        const data = await getPeriods(selectedWeek)
        setPeriods(data)
      } catch (err) {
        console.error('Failed to load periods:', err)
      }
    }
    loadPeriods()
  }, [selectedWeek])

  return (
    <div className="space-y-8">
      {periods ? (
        <div className="bg-white rounded-lg shadow p-6">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">Summary Metrics</h2>
          <MetricsPreview 
            periods={periods}
            baseWeek={selectedWeek}
            onMetricsChange={setMetrics}
          />
        </div>
      ) : (
        <div className="bg-white rounded-lg shadow p-6 text-center">
          <p className="text-gray-600">Loading periods...</p>
        </div>
      )}
    </div>
  )
}

