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
  getWomenCategorySales,
  getSessionsPerCountry,
  getConversionPerCountry,
  getNewCustomersPerCountry,
  getReturningCustomersPerCountry,
  getAOVNewCustomersPerCountry,
  getAOVReturningCustomersPerCountry,
  getMarketingSpendPerCountry,
  getNCACPerCountry,
  getContributionNewPerCountry,
  getContributionNewTotalPerCountry,
  getContributionReturningPerCountry,
  getContributionReturningTotalPerCountry,
  getTotalContributionPerCountry,
  getBatchMetrics,
  type PeriodsResponse,
  type MetricsResponse,
  type MarketsResponse,
  type OnlineKPIsResponse,
  type ContributionResponse,
  type GenderSalesResponse,
  type MenCategorySalesResponse,
  type WomenCategorySalesResponse,
  type SessionsPerCountryResponse,
  type ConversionPerCountryResponse,
  type NewCustomersPerCountryResponse,
  type ReturningCustomersPerCountryResponse,
  type AOVNewCustomersPerCountryResponse,
  type AOVReturningCustomersPerCountryResponse,
  type MarketingSpendPerCountryResponse,
  type nCACPerCountryResponse,
  type ContributionNewPerCountryResponse,
  type ContributionNewTotalPerCountryResponse,
  type ContributionReturningPerCountryResponse,
  type ContributionReturningTotalPerCountryResponse,
  type TotalContributionPerCountryResponse,
  type BatchMetricsResponse
} from '@/lib/api'

interface LoadingProgress {
  step: 'periods' | 'metrics' | 'markets' | 'kpis' | 'contribution' | 'gender_sales' | 'men_category_sales' | 'women_category_sales' | 'sessions_per_country' | 'conversion_per_country' | 'new_customers_per_country' | 'returning_customers_per_country' | 'aov_new_customers_per_country' | 'aov_returning_customers_per_country' | 'marketing_spend_per_country' | 'ncac_per_country' | 'contribution_new_per_country' | 'contribution_new_total_per_country' | 'contribution_returning_per_country' | 'contribution_returning_total_per_country' | 'total_contribution_per_country' | 'complete'
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
  women_category_sales: WomenCategorySalesResponse | null
  sessions_per_country: SessionsPerCountryResponse | null
  conversion_per_country: ConversionPerCountryResponse | null
  new_customers_per_country: NewCustomersPerCountryResponse | null
  returning_customers_per_country: ReturningCustomersPerCountryResponse | null
  aov_new_customers_per_country: AOVNewCustomersPerCountryResponse | null
  aov_returning_customers_per_country: AOVReturningCustomersPerCountryResponse | null
  marketing_spend_per_country: MarketingSpendPerCountryResponse | null
  ncac_per_country: nCACPerCountryResponse | null
  contribution_new_per_country: ContributionNewPerCountryResponse | null
  contribution_new_total_per_country: ContributionNewTotalPerCountryResponse | null
  contribution_returning_per_country: ContributionReturningPerCountryResponse | null
  contribution_returning_total_per_country: ContributionReturningTotalPerCountryResponse | null
  total_contribution_per_country: TotalContributionPerCountryResponse | null
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
  women_category_sales: WomenCategorySalesResponse | null
  sessions_per_country: SessionsPerCountryResponse | null
  conversion_per_country: ConversionPerCountryResponse | null
  new_customers_per_country: NewCustomersPerCountryResponse | null
  returning_customers_per_country: ReturningCustomersPerCountryResponse | null
  aov_new_customers_per_country: AOVNewCustomersPerCountryResponse | null
  aov_returning_customers_per_country: AOVReturningCustomersPerCountryResponse | null
  marketing_spend_per_country: MarketingSpendPerCountryResponse | null
  ncac_per_country: nCACPerCountryResponse | null
  contribution_new_per_country: ContributionNewPerCountryResponse | null
  contribution_new_total_per_country: ContributionNewTotalPerCountryResponse | null
  contribution_returning_per_country: ContributionReturningPerCountryResponse | null
  contribution_returning_total_per_country: ContributionReturningTotalPerCountryResponse | null
  total_contribution_per_country: TotalContributionPerCountryResponse | null
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
  const [women_category_sales, setWomen_category_sales] = useState<WomenCategorySalesResponse | null>(null)
  const [sessions_per_country, setSessions_per_country] = useState<SessionsPerCountryResponse | null>(null)
  const [conversion_per_country, setConversion_per_country] = useState<ConversionPerCountryResponse | null>(null)
  const [new_customers_per_country, setNew_customers_per_country] = useState<NewCustomersPerCountryResponse | null>(null)
  const [returning_customers_per_country, setReturning_customers_per_country] = useState<ReturningCustomersPerCountryResponse | null>(null)
  const [aov_new_customers_per_country, setAov_new_customers_per_country] = useState<AOVNewCustomersPerCountryResponse | null>(null)
  const [aov_returning_customers_per_country, setAov_returning_customers_per_country] = useState<AOVReturningCustomersPerCountryResponse | null>(null)
  const [marketing_spend_per_country, setMarketing_spend_per_country] = useState<MarketingSpendPerCountryResponse | null>(null)
  const [ncac_per_country, setNcac_per_country] = useState<nCACPerCountryResponse | null>(null)
  const [contribution_new_per_country, setContribution_new_per_country] = useState<ContributionNewPerCountryResponse | null>(null)
  const [contribution_new_total_per_country, setContribution_new_total_per_country] = useState<ContributionNewTotalPerCountryResponse | null>(null)
  const [contribution_returning_per_country, setContribution_returning_per_country] = useState<ContributionReturningPerCountryResponse | null>(null)
  const [contribution_returning_total_per_country, setContribution_returning_total_per_country] = useState<ContributionReturningTotalPerCountryResponse | null>(null)
  const [total_contribution_per_country, setTotal_contribution_per_country] = useState<TotalContributionPerCountryResponse | null>(null)
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
        setWomen_category_sales(cached.women_category_sales)
        setSessions_per_country(cached.sessions_per_country)
        setConversion_per_country(cached.conversion_per_country)
        setNew_customers_per_country(cached.new_customers_per_country)
        setReturning_customers_per_country(cached.returning_customers_per_country)
        setAov_new_customers_per_country(cached.aov_new_customers_per_country)
        setAov_returning_customers_per_country(cached.aov_returning_customers_per_country)
        setMarketing_spend_per_country(cached.marketing_spend_per_country)
        setNcac_per_country(cached.ncac_per_country)
        setContribution_new_per_country(cached.contribution_new_per_country)
        setContribution_new_total_per_country(cached.contribution_new_total_per_country)
        setContribution_returning_per_country(cached.contribution_returning_per_country)
        setContribution_returning_total_per_country(cached.contribution_returning_total_per_country)
        setTotal_contribution_per_country(cached.total_contribution_per_country)
        return
      }
    }

    setLoading(true)

    try {
      // Try to load all data via batch endpoint first (fallback to individual calls)
      setLoadingProgress({ 
        step: 'metrics', 
        stepNumber: 1, 
        totalSteps: 21, 
        message: 'Loading all metrics in batch...', 
        percentage: 5 
      })
      
      let batchMode = false
      try {
        // Try batch endpoint
        const batchData = await getBatchMetrics(week, 8)
        batchMode = true
        
        // Set all data from batch response
        setPeriods(batchData.periods)
        setMetrics(batchData.metrics)
        setMarkets(batchData.markets)
        setKpis(batchData.kpis)
        setContribution(batchData.contribution)
        setGender_sales(batchData.gender_sales)
        setMen_category_sales(batchData.men_category_sales)
        setWomen_category_sales(batchData.women_category_sales)
        setSessions_per_country(batchData.sessions_per_country)
        setConversion_per_country(batchData.conversion_per_country)
        setNew_customers_per_country(batchData.new_customers_per_country)
        setReturning_customers_per_country(batchData.returning_customers_per_country)
        setAov_new_customers_per_country(batchData.aov_new_customers_per_country)
        setAov_returning_customers_per_country(batchData.aov_returning_customers_per_country)
        setMarketing_spend_per_country(batchData.marketing_spend_per_country)
        setNcac_per_country(batchData.ncac_per_country)
        setContribution_new_per_country(batchData.contribution_new_per_country)
        setContribution_new_total_per_country(batchData.contribution_new_total_per_country)
        setContribution_returning_per_country(batchData.contribution_returning_per_country)
        setContribution_returning_total_per_country(batchData.contribution_returning_total_per_country)
        setTotal_contribution_per_country(batchData.total_contribution_per_country)
        
        setLoadingProgress({ 
          step: 'complete', 
          stepNumber: 21, 
          totalSteps: 21, 
          message: 'Complete!', 
          percentage: 100 
        })
        
        // Save to cache
        saveCache(week, {
          periods: batchData.periods,
          metrics: batchData.metrics,
          markets: batchData.markets,
          kpis: batchData.kpis,
          contribution: batchData.contribution,
          gender_sales: batchData.gender_sales,
          men_category_sales: batchData.men_category_sales,
          women_category_sales: batchData.women_category_sales,
          sessions_per_country: batchData.sessions_per_country,
          conversion_per_country: batchData.conversion_per_country,
          new_customers_per_country: batchData.new_customers_per_country,
          returning_customers_per_country: batchData.returning_customers_per_country,
          aov_new_customers_per_country: batchData.aov_new_customers_per_country,
          aov_returning_customers_per_country: batchData.aov_returning_customers_per_country,
          marketing_spend_per_country: batchData.marketing_spend_per_country,
          ncac_per_country: batchData.ncac_per_country,
          contribution_new_per_country: batchData.contribution_new_per_country,
          contribution_new_total_per_country: batchData.contribution_new_total_per_country,
          contribution_returning_per_country: batchData.contribution_returning_per_country,
          contribution_returning_total_per_country: batchData.contribution_returning_total_per_country,
          total_contribution_per_country: batchData.total_contribution_per_country,
          timestamp: Date.now()
        })
        
        setLoading(false)
        return
      } catch (batchError) {
        console.warn('Batch endpoint failed, falling back to individual calls:', batchError)
        // Fall through to individual calls
      }
      
      // Individual calls (fallback or primary if batch disabled)
      if (!batchMode) {
        // Step 1: Load periods
      setLoadingProgress({ 
        step: 'periods', 
        stepNumber: 1, 
        totalSteps: 21, 
        message: 'Loading periods...', 
        percentage: 0 
      })
      const periodsData = await getPeriods(week)
      setPeriods(periodsData)

      // Step 2: Load metrics
      setLoadingProgress({ 
        step: 'metrics', 
        stepNumber: 2, 
        totalSteps: 8, 
        message: 'Loading summary metrics...', 
        percentage: 12 
      })
      const metricsData = await getTable1Metrics(week, ['actual', 'last_week', 'last_year', 'year_2023'], true)
      setMetrics(metricsData)

      // Step 3: Load markets
      setLoadingProgress({ 
        step: 'markets', 
        stepNumber: 3, 
        totalSteps: 8, 
        message: 'Loading top markets data...', 
        percentage: 25 
      })
      const marketsData = await getTopMarkets(week, 8)
      setMarkets(marketsData)

      // Step 4: Load KPIs
      setLoadingProgress({ 
        step: 'kpis', 
        stepNumber: 4, 
        totalSteps: 8, 
        message: 'Loading online KPIs...', 
        percentage: 37 
      })
      const kpisData = await getOnlineKPIs(week, 8)
      setKpis(kpisData)

      // Step 5: Load Contribution
      setLoadingProgress({ 
        step: 'contribution', 
        stepNumber: 5, 
        totalSteps: 8, 
        message: 'Loading contribution metrics...', 
        percentage: 50 
      })
      const contributionData = await getContribution(week, 8)
      setContribution(contributionData)

      // Step 6: Load Gender Sales
      setLoadingProgress({ 
        step: 'gender_sales', 
        stepNumber: 6, 
        totalSteps: 8, 
        message: 'Loading gender sales data...', 
        percentage: 62 
      })
      const genderSalesData = await getGenderSales(week, 8)
      setGender_sales(genderSalesData)

      // Step 7: Load Men Category Sales
      setLoadingProgress({ 
        step: 'men_category_sales', 
        stepNumber: 7, 
        totalSteps: 8, 
        message: 'Loading men category sales...', 
        percentage: 75 
      })
      const menCategorySalesData = await getMenCategorySales(week, 8)
      setMen_category_sales(menCategorySalesData)

      // Step 8: Load Women Category Sales
      setLoadingProgress({ 
        step: 'women_category_sales', 
        stepNumber: 8, 
        totalSteps: 9, 
        message: 'Loading women category sales...', 
        percentage: 87 
      })
      const womenCategorySalesData = await getWomenCategorySales(week, 8)
      setWomen_category_sales(womenCategorySalesData)

      // Step 9: Load Sessions per Country
      setLoadingProgress({ 
        step: 'sessions_per_country', 
        stepNumber: 9, 
        totalSteps: 10, 
        message: 'Loading sessions per country...', 
        percentage: 90 
      })
      const sessionsPerCountryData = await getSessionsPerCountry(week, 8)
      setSessions_per_country(sessionsPerCountryData)

      // Step 10: Load Conversion per Country
      setLoadingProgress({ 
        step: 'conversion_per_country', 
        stepNumber: 10, 
        totalSteps: 11, 
        message: 'Loading conversion per country...', 
        percentage: 90 
      })
      const conversionPerCountryData = await getConversionPerCountry(week, 8)
      setConversion_per_country(conversionPerCountryData)

      // Step 11: Load New Customers per Country
      setLoadingProgress({ 
        step: 'new_customers_per_country', 
        stepNumber: 11, 
        totalSteps: 12, 
        message: 'Loading new customers per country...', 
        percentage: 92 
      })
      const newCustomersPerCountryData = await getNewCustomersPerCountry(week, 8)
      setNew_customers_per_country(newCustomersPerCountryData)

      // Step 12: Load Returning Customers per Country
      setLoadingProgress({ 
        step: 'returning_customers_per_country', 
        stepNumber: 12, 
        totalSteps: 13, 
        message: 'Loading returning customers per country...', 
        percentage: 92 
      })
      const returningCustomersPerCountryData = await getReturningCustomersPerCountry(week, 8)
      setReturning_customers_per_country(returningCustomersPerCountryData)

      // Step 13: Load AOV New Customers per Country
      setLoadingProgress({ 
        step: 'aov_new_customers_per_country', 
        stepNumber: 13, 
        totalSteps: 14, 
        message: 'Loading AOV new customers per country...', 
        percentage: 93 
      })
      const aovNewCustomersPerCountryData = await getAOVNewCustomersPerCountry(week, 8)
      setAov_new_customers_per_country(aovNewCustomersPerCountryData)

      // Step 14: Load AOV Returning Customers per Country
      setLoadingProgress({ 
        step: 'aov_returning_customers_per_country', 
        stepNumber: 14, 
        totalSteps: 15, 
        message: 'Loading AOV returning customers per country...', 
        percentage: 93 
      })
      const aovReturningCustomersPerCountryData = await getAOVReturningCustomersPerCountry(week, 8)
      setAov_returning_customers_per_country(aovReturningCustomersPerCountryData)

      // Step 15: Load Marketing Spend per Country
      setLoadingProgress({ 
        step: 'marketing_spend_per_country', 
        stepNumber: 15, 
        totalSteps: 16, 
        message: 'Loading marketing spend per country...', 
        percentage: 94 
      })
      const marketingSpendPerCountryData = await getMarketingSpendPerCountry(week, 8)
      setMarketing_spend_per_country(marketingSpendPerCountryData)

      // Step 16: Load nCAC per Country
      setLoadingProgress({ 
        step: 'ncac_per_country', 
        stepNumber: 16, 
        totalSteps: 17, 
        message: 'Loading nCAC per country...', 
        percentage: 94 
      })
      const ncacPerCountryData = await getNCACPerCountry(week, 8)
      setNcac_per_country(ncacPerCountryData)

      // Step 17: Load Contribution New per Country
      setLoadingProgress({ 
        step: 'contribution_new_per_country', 
        stepNumber: 17, 
        totalSteps: 18, 
        message: 'Loading contribution per new customer per country...', 
        percentage: 94 
      })
      const contributionNewPerCountryData = await getContributionNewPerCountry(week, 8)
      setContribution_new_per_country(contributionNewPerCountryData)

      // Step 18: Load Contribution New Total per Country
      setLoadingProgress({ 
        step: 'contribution_new_total_per_country', 
        stepNumber: 18, 
        totalSteps: 20, 
        message: 'Loading total contribution per country...', 
        percentage: 90 
      })
      const contributionNewTotalPerCountryData = await getContributionNewTotalPerCountry(week, 8)
      setContribution_new_total_per_country(contributionNewTotalPerCountryData)

      // Step 19: Load Contribution Returning per Country
      setLoadingProgress({ 
        step: 'contribution_returning_per_country', 
        stepNumber: 19, 
        totalSteps: 20, 
        message: 'Loading contribution per returning customer per country...', 
        percentage: 95 
      })
      const contributionReturningPerCountryData = await getContributionReturningPerCountry(week, 8)
      setContribution_returning_per_country(contributionReturningPerCountryData)

      // Step 20: Load Contribution Returning Total per Country
      setLoadingProgress({ 
        step: 'contribution_returning_total_per_country', 
        stepNumber: 20, 
        totalSteps: 21, 
        message: 'Loading total contribution per returning customers by country...', 
        percentage: 95 
      })
      const contributionReturningTotalPerCountryData = await getContributionReturningTotalPerCountry(week, 8)
      setContribution_returning_total_per_country(contributionReturningTotalPerCountryData)

      // Step 21: Load Total Contribution per Country
      setLoadingProgress({ 
        step: 'total_contribution_per_country', 
        stepNumber: 21, 
        totalSteps: 21, 
        message: 'Loading total contribution for all customers by country...', 
        percentage: 97 
      })
      const totalContributionPerCountryData = await getTotalContributionPerCountry(week, 8)
      setTotal_contribution_per_country(totalContributionPerCountryData)

      setLoadingProgress({ 
        step: 'complete', 
        stepNumber: 21, 
        totalSteps: 21, 
        message: 'Complete!', 
        percentage: 100 
      })

      // Save to cache (individual calls mode)
      if (!batchMode) {
        saveCache(week, {
          periods: periodsData,
          metrics: metricsData,
          markets: marketsData,
          kpis: kpisData,
          contribution: contributionData,
          gender_sales: genderSalesData,
          men_category_sales: menCategorySalesData,
          women_category_sales: womenCategorySalesData,
          sessions_per_country: sessionsPerCountryData,
          conversion_per_country: conversionPerCountryData,
          new_customers_per_country: newCustomersPerCountryData,
          returning_customers_per_country: returningCustomersPerCountryData,
          aov_new_customers_per_country: aovNewCustomersPerCountryData,
          aov_returning_customers_per_country: aovReturningCustomersPerCountryData,
          marketing_spend_per_country: marketingSpendPerCountryData,
          ncac_per_country: ncacPerCountryData,
          contribution_new_per_country: contributionNewPerCountryData,
          contribution_new_total_per_country: contributionNewTotalPerCountryData,
          contribution_returning_per_country: contributionReturningPerCountryData,
          contribution_returning_total_per_country: contributionReturningTotalPerCountryData,
          total_contribution_per_country: totalContributionPerCountryData,
          timestamp: Date.now()
        })
        }
      }
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
      setWomen_category_sales(null)
      setSessions_per_country(null)
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
    women_category_sales,
    sessions_per_country,
    conversion_per_country,
    new_customers_per_country,
    returning_customers_per_country,
    aov_new_customers_per_country,
    aov_returning_customers_per_country,
    marketing_spend_per_country,
    ncac_per_country,
    contribution_new_per_country,
    contribution_new_total_per_country,
    contribution_returning_per_country,
    contribution_returning_total_per_country,
    total_contribution_per_country,
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

export function useWomenCategorySales() {
  const { women_category_sales } = useDataCache()
  return { women_category_sales }
}

export function useSessionsPerCountry() {
  const { sessions_per_country } = useDataCache()
  return { sessions_per_country }
}

export function useConversionPerCountry() {
  const { conversion_per_country } = useDataCache()
  return { conversion_per_country }
}

export function useNewCustomersPerCountry() {
  const { new_customers_per_country } = useDataCache()
  return { new_customers_per_country }
}

export function useReturningCustomersPerCountry() {
  const { returning_customers_per_country } = useDataCache()
  return { returning_customers_per_country }
}

export function useAOVNewCustomersPerCountry() {
  const { aov_new_customers_per_country } = useDataCache()
  return { aov_new_customers_per_country }
}

export function useAOVReturningCustomersPerCountry() {
  const { aov_returning_customers_per_country } = useDataCache()
  return { aov_returning_customers_per_country }
}

export function useMarketingSpendPerCountry() {
  const { marketing_spend_per_country } = useDataCache()
  return { marketing_spend_per_country }
}

export function useNCACPerCountry() {
  const { ncac_per_country } = useDataCache()
  return { ncac_per_country }
}

export function useContributionNewPerCountry() {
  const { contribution_new_per_country } = useDataCache()
  return { contribution_new_per_country }
}

export function useContributionNewTotalPerCountry() {
  const { contribution_new_total_per_country } = useDataCache()
  return { contribution_new_total_per_country }
}

export function useContributionReturningPerCountry() {
  const { contribution_returning_per_country } = useDataCache()
  return { contribution_returning_per_country }
}

export function useContributionReturningTotalPerCountry() {
  const { contribution_returning_total_per_country } = useDataCache()
  return { contribution_returning_total_per_country }
}

export function useTotalContributionPerCountry() {
  const { total_contribution_per_country } = useDataCache()
  return { total_contribution_per_country }
}
