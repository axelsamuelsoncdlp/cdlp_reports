'use client'

import { createContext, useContext, useState, useEffect, useCallback, ReactNode } from 'react'
import { 
  getPeriods, 
  getTable1Metrics, 
  getTopMarkets, 
  getOnlineKPIs,
  getContribution,
  getGenderSales,
  getMenCategorySales,
  type PeriodsResponse,
  type MetricsResponse,
  type MarketsResponse,
  type OnlineKPIsResponse,
  type ContributionResponse,
  type GenderSalesResponse,
  type MenCategorySalesResponse
} from '@/lib/api'

interface LoadingProgress {
  step: 'periods' | 'metrics' | 'markets' | 'kpis' | 'contribution' | 'gender_sales' | 'men_category_sales' | 'complete'
  stepNumber: number
  totalSteps: number
  message: string
  percentage: number
}

interface CacheData {
  periods: PeriodsResponse | null
  metrics: MetricsResponse | null
  markets: MarketsResponse | null
  kpis: OnlineKPIsResponse | null
  contribution: ContributionResponse | null
  gender_sales: GenderSalesResponse | null
  men_category_sales: MenCategorySalesResponse | null
  timestamp: number
}

interface DataCacheContextType {
  periods: PeriodsResponse | null
  metrics: MetricsResponse | null
  markets: MarketsResponse | null
  kpis: OnlineKPIsResponse | null
  contribution: ContributionResponse | null
  gender_sales: GenderSalesResponse | null
  men_category_sales: MenCategorySalesResponse | null
  loading: boolean
  error: string | null
  loadingProgress: LoadingProgress | null
  loadAllData: (baseWeek: string, forceRefresh?: boolean) => Promise<void>
  refreshData: () => Promise<void>
  clearCache: () => void
  baseWeek: string
  setBaseWeek: (week: string) => void
}

const DataCacheContext = createContext<DataCacheContextType | undefined>(undefined)

const CACHE_EXPIRY = 60 * 60 * 1000 // 1 hour
const DEFAULT_BASE_WEEK = '2025-42'

export function DataCacheProvider({ children }: { children: ReactNode }) {
  const [periods, setPeriods] = useState<PeriodsResponse | null>(null)
  const [metrics, setMetrics] = useState<MetricsResponse | null>(null)
  const [markets, setMarkets] = useState<MarketsResponse | null>(null)
  const [kpis, setKpis] = useState<OnlineKPIsResponse | null>(null)
  const [contribution, setContribution] = useState<ContributionResponse | null>(null)
  const [gender_sales, setGender_sales] = useState<GenderSalesResponse | null>(null)
  const [men_category_sales, setMen_category_sales] = useState<MenCategorySalesResponse | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [loadingProgress, setLoadingProgress] = useState<LoadingProgress | null>(null)
  const [baseWeek, setBaseWeek] = useState<string>(DEFAULT_BASE_WEEK)

  const getCacheKey = (week: string) => `dashboard_cache_${week}`

  const getCachedData = (week: string): CacheData | null => {
    try {
      const cached = localStorage.getItem(getCacheKey(week))
      if (!cached) return null
      
      const parsed: CacheData = JSON.parse(cached)
      const cacheAge = Date.now() - parsed.timestamp
      
      if (cacheAge > CACHE_EXPIRY) {
        localStorage.removeItem(getCacheKey(week))
        return null
      }
      
      return parsed
    } catch (err) {
      console.warn('Failed to load cache:', err)
      return null
    }
  }

  const saveCache = (week: string, data: CacheData) => {
    try {
      localStorage.setItem(getCacheKey(week), JSON.stringify(data))
    } catch (err) {
      console.warn('Failed to save cache:', err)
    }
  }

  const loadAllData = useCallback(async (week: string, forceRefresh = false) => {
    setError(null)

    // Check cache first
    if (!forceRefresh) {
      const cached = getCachedData(week)
      if (cached) {
        setPeriods(cached.periods)
        setMetrics(cached.metrics)
        setMarkets(cached.markets)
        setKpis(cached.kpis)
        setContribution(cached.contribution)
        setGender_sales(cached.gender_sales)
        setMen_category_sales(cached.men_category_sales)
        return
      }
    }

    setLoading(true)

    try {
      // Step 1: Load periods
      setLoadingProgress({ 
        step: 'periods', 
        stepNumber: 1, 
        totalSteps: 7, 
        message: 'Loading periods...', 
        percentage: 0 
      })
      const periodsData = await getPeriods(week)
      setPeriods(periodsData)

      // Step 2: Load metrics
      setLoadingProgress({ 
        step: 'metrics', 
        stepNumber: 2, 
        totalSteps: 7, 
        message: 'Loading summary metrics...', 
        percentage: 14 
      })
      const metricsData = await getTable1Metrics(week, ['actual', 'last_week', 'last_year', 'year_2023'], true)
      setMetrics(metricsData)

      // Step 3: Load markets
      setLoadingProgress({ 
        step: 'markets', 
        stepNumber: 3, 
        totalSteps: 7, 
        message: 'Loading top markets data...', 
        percentage: 28 
      })
      const marketsData = await getTopMarkets(week, 8)
      setMarkets(marketsData)

      // Step 4: Load KPIs
      setLoadingProgress({ 
        step: 'kpis', 
        stepNumber: 4, 
        totalSteps: 7, 
        message: 'Loading online KPIs...', 
        percentage: 42 
      })
      const kpisData = await getOnlineKPIs(week, 8)
      setKpis(kpisData)

      // Step 5: Load Contribution
      setLoadingProgress({ 
        step: 'contribution', 
        stepNumber: 5, 
        totalSteps: 7, 
        message: 'Loading contribution metrics...', 
        percentage: 57 
      })
      const contributionData = await getContribution(week, 8)
      setContribution(contributionData)

      // Step 6: Load Gender Sales
      setLoadingProgress({ 
        step: 'gender_sales', 
        stepNumber: 6, 
        totalSteps: 7, 
        message: 'Loading gender sales data...', 
        percentage: 71 
      })
      const genderSalesData = await getGenderSales(week, 8)
      setGender_sales(genderSalesData)

      // Step 7: Load Men Category Sales
      setLoadingProgress({ 
        step: 'men_category_sales', 
        stepNumber: 7, 
        totalSteps: 7, 
        message: 'Loading men category sales...', 
        percentage: 85 
      })
      const menCategorySalesData = await getMenCategorySales(week, 8)
      setMen_category_sales(menCategorySalesData)

      setLoadingProgress({ 
        step: 'complete', 
        stepNumber: 7, 
        totalSteps: 7, 
        message: 'Complete!', 
        percentage: 100 
      })

      // Save to cache
      saveCache(week, {
        periods: periodsData,
        metrics: metricsData,
        markets: marketsData,
        kpis: kpisData,
        contribution: contributionData,
        gender_sales: genderSalesData,
        men_category_sales: menCategorySalesData,
        timestamp: Date.now()
      })
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load dashboard data')
      console.error('Error loading dashboard data:', err)
    } finally {
      setLoading(false)
      // Clear progress after a short delay
      setTimeout(() => setLoadingProgress(null), 500)
    }
  }, [])

  const refreshData = useCallback(async () => {
    await loadAllData(baseWeek, true)
  }, [loadAllData, baseWeek])

  const clearCache = useCallback(() => {
    try {
      localStorage.removeItem(getCacheKey(baseWeek))
      setPeriods(null)
      setMetrics(null)
      setMarkets(null)
      setKpis(null)
      setContribution(null)
      setGender_sales(null)
      setMen_category_sales(null)
    } catch (err) {
      console.warn('Failed to clear cache:', err)
    }
  }, [baseWeek])

  // Load data on mount and when baseWeek changes
  useEffect(() => {
    loadAllData(baseWeek)
  }, [loadAllData, baseWeek])

  const value: DataCacheContextType = {
    periods,
    metrics,
    markets,
    kpis,
    contribution,
    gender_sales,
    men_category_sales,
    loading,
    error,
    loadingProgress,
    loadAllData,
    refreshData,
    clearCache,
    baseWeek,
    setBaseWeek
  }

  return <DataCacheContext.Provider value={value}>{children}</DataCacheContext.Provider>
}

export function useDataCache() {
  const context = useContext(DataCacheContext)
  if (context === undefined) {
    throw new Error('useDataCache must be used within DataCacheProvider')
  }
  return context
}

export function usePeriods() {
  const { periods } = useDataCache()
  return periods
}

export function useMetrics() {
  const { metrics } = useDataCache()
  return { metrics }
}

export function useMarkets() {
  const { markets } = useDataCache()
  return { markets }
}

export function useKPIs() {
  const { kpis } = useDataCache()
  return { kpis }
}

export function useContribution() {
  const { contribution } = useDataCache()
  return { contributions: contribution }
}

export function useGenderSales() {
  const { gender_sales } = useDataCache()
  return { gender_sales }
}

export function useMenCategorySales() {
  const { men_category_sales } = useDataCache()
  return { men_category_sales }
}
