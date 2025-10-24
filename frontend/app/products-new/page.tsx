'use client'

import { useState, useEffect } from 'react'
import ProductsNewTable from '@/components/ProductsNewTable'
import { getPeriods } from '@/lib/api'
import { Loader2 } from 'lucide-react'
import { Skeleton } from '@/components/ui/skeleton'

export default function ProductsNew() {
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
        <div className="grid grid-cols-2 gap-6">
          <div className="bg-white rounded-lg shadow p-6">
            <h2 className="text-lg font-semibold text-gray-900 mb-4">Products New</h2>
            <ProductsNewTable baseWeek={selectedWeek} customerType="new" />
          </div>
          <div className="bg-white rounded-lg shadow p-6">
            <h2 className="text-lg font-semibold text-gray-900 mb-4">Products Returning</h2>
            <ProductsNewTable baseWeek={selectedWeek} customerType="returning" />
          </div>
        </div>
      ) : (
        <div className="space-y-4">
          <div className="flex items-center gap-3">
            <Loader2 className="h-6 w-6 animate-spin text-primary" />
            <div>
              <h2 className="text-lg font-semibold text-gray-900">Loading Products</h2>
              <p className="text-sm text-gray-600">Initializing data...</p>
            </div>
          </div>
          <div className="bg-white rounded-lg shadow p-6">
            <Skeleton className="h-96 w-full" />
          </div>
        </div>
      )}
    </div>
  )
}

