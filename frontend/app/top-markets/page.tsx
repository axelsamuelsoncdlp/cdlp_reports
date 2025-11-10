'use client'

import TopMarketsTable from '@/components/TopMarketsTable'
import { useDataCache } from '@/contexts/DataCacheContext'

export default function TopMarkets() {
  const { baseWeek } = useDataCache()

  return (
    <div className="space-y-8">
      <div className="bg-white rounded-lg shadow p-6">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">Top Markets</h2>
        <TopMarketsTable baseWeek={baseWeek} />
      </div>
    </div>
  )
}

