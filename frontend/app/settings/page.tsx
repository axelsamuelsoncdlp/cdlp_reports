'use client'

import { useState } from 'react'
import PeriodSelector from '@/components/PeriodSelector'
import GenerateButton from '@/components/GenerateButton'

export default function Settings() {
  const [selectedWeek, setSelectedWeek] = useState('2025-42')
  const [periods, setPeriods] = useState(null)
  const [metrics, setMetrics] = useState(null)
  const [isGenerating, setIsGenerating] = useState(false)

  return (
    <div className="space-y-8">
      <div className="bg-white rounded-lg shadow p-6">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">Select Period</h2>
        <PeriodSelector 
          selectedWeek={selectedWeek}
          onWeekChange={setSelectedWeek}
          onPeriodsChange={setPeriods}
        />
      </div>

      {periods && (
        <div className="bg-white rounded-lg shadow p-6">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">Generate Report</h2>
          {metrics && (
            <GenerateButton 
              baseWeek={selectedWeek}
              periods={periods}
              metrics={metrics}
              isGenerating={isGenerating}
              onGeneratingChange={setIsGenerating}
            />
          )}
        </div>
      )}
    </div>
  )
}

