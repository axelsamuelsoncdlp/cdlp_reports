'use client'

import { useDataCache } from '@/contexts/DataCacheContext'
import LoadingProgress from '@/components/LoadingProgress'

export default function LayoutContent({ children }: { children: React.ReactNode }) {
  const { loading, loadingProgress } = useDataCache()

  if (loading && loadingProgress) {
    return <LoadingProgress progress={loadingProgress} />
  }

  return <>{children}</>
}

