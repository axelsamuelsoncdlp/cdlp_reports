'use client'

import { useEffect, useState } from 'react'
import CategorySalesTable from '@/components/CategorySalesTable'
import { Loader2 } from 'lucide-react'
import { Skeleton } from '@/components/ui/skeleton'
import { useDataCache } from '@/contexts/DataCacheContext'

export default function CategorySales() {
  const { baseWeek } = useDataCache()
  const [periods, setPeriods] = useState<any>(null)

  // Use periods from cache instead of loading automatically
  const { periods: cachedPeriods } = useDataCache()
  
  useEffect(() => {
    // Only use cached periods - don't auto-load
    if (cachedPeriods) {
      setPeriods(cachedPeriods as any)
    }
  }, [cachedPeriods])

  return (
    <div className="space-y-8">
      {periods ? (
        <div className="bg-white rounded-lg shadow p-6">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">Category Sales</h2>
          <CategorySalesTable baseWeek={baseWeek} />
        </div>
      ) : (
        <div className="space-y-4">
          <div className="flex items-center gap-3">
            <Loader2 className="h-6 w-6 animate-spin text-primary" />
            <div>
              <h2 className="text-lg font-semibold text-gray-900">Loading Category Sales</h2>
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

