'use client'

import { useState, useEffect } from 'react'
import { getPeriods } from '@/lib/api'

export default function OnlineKPIs() {
  const [selectedWeek, setSelectedWeek] = useState('2025-42')
  const [periods, setPeriods] = useState(null)

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
          <h2 className="text-lg font-semibold text-gray-900 mb-4">Online KPIs</h2>
          <div className="bg-blue-50 border border-blue-200 rounded-lg p-6 text-center">
            <div className="text-blue-800 text-sm font-medium mb-2">
              Online KPIs
            </div>
            <div className="text-blue-600 text-xs">
              Coming soon...
            </div>
          </div>
        </div>
      ) : (
        <div className="bg-white rounded-lg shadow p-6 text-center">
          <p className="text-gray-600">Loading periods...</p>
        </div>
      )}
    </div>
  )
}

