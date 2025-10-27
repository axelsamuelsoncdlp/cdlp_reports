'use client'

import { useEffect, useState } from 'react'
import ProductsGenderTable from '@/components/ProductsGenderTable'
import { getPeriods } from '@/lib/api'
import { Loader2 } from 'lucide-react'
import { Skeleton } from '@/components/ui/skeleton'
import { useDataCache } from '@/contexts/DataCacheContext'

export default function ProductsGender() {
  const { baseWeek } = useDataCache()
  const [periods, setPeriods] = useState(null)

  // Load periods on mount and when baseWeek changes
  useEffect(() => {
    const loadPeriods = async () => {
      if (!baseWeek) return
      try {
        const data = await getPeriods(baseWeek)
        setPeriods(data)
      } catch (err) {
        console.error('Failed to load periods:', err)
      }
    }
    loadPeriods()
  }, [baseWeek])

  return (
    <div className="space-y-8">
      {periods ? (
        <div className="grid grid-cols-2 gap-6">
          <div className="bg-white rounded-lg shadow p-6">
            <h2 className="text-lg font-semibold text-gray-900 mb-4">Products Men</h2>
            <ProductsGenderTable baseWeek={baseWeek} genderFilter="men" />
          </div>
          <div className="bg-white rounded-lg shadow p-6">
            <h2 className="text-lg font-semibold text-gray-900 mb-4">Products Women</h2>
            <ProductsGenderTable baseWeek={baseWeek} genderFilter="women" />
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

