const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

export interface PeriodsResponse {
  actual: string
  last_week: string
  last_year: string
  year_2023: string
  date_ranges: Record<string, {
    start: string
    end: string
    display: string
  }>
  ytd_periods: Record<string, {
    start: string
    end: string
  }>
}

export interface MetricsResponse {
  periods: Record<string, Record<string, number>>
}

export interface MarketsResponse {
  markets: Array<{
    country: string
    weeks: Record<string, number>
    average: number
  }>
  period_info: {
    latest_week: string
    latest_dates: string
  }
}

export interface OnlineKPIsResponse {
  kpis: Array<{
    week: string
    aov_new_customer: number
    aov_returning_customer: number
    cos: number
    marketing_spend: number
    conversion_rate: number
    new_customers: number
    returning_customers: number
    sessions: number
    new_customer_cac: number
    total_orders: number
    last_year: {
      week: string
      aov_new_customer: number
      aov_returning_customer: number
      cos: number
      marketing_spend: number
      conversion_rate: number
      new_customers: number
      returning_customers: number
      sessions: number
      new_customer_cac: number
      total_orders: number
    } | null
  }>
  period_info: {
    latest_week: string
    latest_dates: string
  }
}

export interface ContributionData {
  week: string
  gross_revenue_new: number
  gross_revenue_returning: number
  contribution_new: number
  contribution_returning: number
  contribution_total: number
  last_year: {
    week: string
    gross_revenue_new: number
    gross_revenue_returning: number
    contribution_new: number
    contribution_returning: number
    contribution_total: number
  } | null
}

export interface ContributionResponse {
  contributions: ContributionData[]
  period_info: {
    latest_week: string
    latest_dates: string
  }
}

export interface GenderSalesData {
  week: string
  men_unisex_sales: number
  women_sales: number
  total_sales: number
  last_year: {
    week: string
    men_unisex_sales: number
    women_sales: number
    total_sales: number
  } | null
}

export interface GenderSalesResponse {
  gender_sales: GenderSalesData[]
  period_info: {
    latest_week: string
    latest_dates: string
  }
}

export interface MenCategorySalesData {
  week: string
  categories: Record<string, number>
  last_year: {
    week: string
    categories: Record<string, number>
  } | null
}

export interface MenCategorySalesResponse {
  men_category_sales: MenCategorySalesData[]
  period_info: {
    latest_week: string
    latest_dates: string
  }
}

export interface WomenCategorySalesData {
  week: string
  categories: Record<string, number>
  last_year: {
    week: string
    categories: Record<string, number>
  } | null
}

export interface WomenCategorySalesResponse {
  women_category_sales: WomenCategorySalesData[]
  period_info: {
    latest_week: string
    latest_dates: string
  }
}

export interface CategorySalesData {
  week: string
  categories: Record<string, number>
  last_year: {
    week: string
    categories: Record<string, number>
  } | null
}

export interface CategorySalesResponse {
  category_sales: CategorySalesData[]
  period_info: {
    latest_week: string
    latest_dates: string
  }
}

export interface GeneratePDFResponse {
  success: boolean
  file_path: string
  download_url: string
}

export async function getPeriods(baseWeek: string): Promise<PeriodsResponse> {
  const response = await fetch(`${API_BASE_URL}/api/periods?base_week=${baseWeek}`)
  if (!response.ok) {
    throw new Error(`Failed to fetch periods: ${response.statusText}`)
  }
  return response.json()
}

export async function getTable1Metrics(baseWeek: string, periods: string[], includeYtd: boolean = true): Promise<MetricsResponse> {
  const periodsParam = periods.join(',')
  const response = await fetch(`${API_BASE_URL}/api/metrics/table1?base_week=${baseWeek}&periods=${periodsParam}&include_ytd=${includeYtd}`)
  if (!response.ok) {
    throw new Error(`Failed to fetch metrics: ${response.statusText}`)
  }
  return response.json()
}

export async function getTopMarkets(baseWeek: string, numWeeks: number = 8): Promise<MarketsResponse> {
  try {
    const response = await fetch(`${API_BASE_URL}/api/markets/top?base_week=${baseWeek}&num_weeks=${numWeeks}`, {
      signal: AbortSignal.timeout(60000) // 60 second timeout
    })
    if (!response.ok) {
      throw new Error(`Failed to fetch markets: ${response.statusText}`)
    }
    return response.json()
  } catch (error: any) {
    if (error.name === 'TimeoutError' || error.name === 'AbortError') {
      throw new Error(`Request timeout: Backend server may be slow or unresponsive`)
    }
    if (error.message?.includes('Failed to fetch') || error.message?.includes('NetworkError')) {
      throw new Error(`Network error: Unable to connect to backend server at ${API_BASE_URL}. Please check if the server is running.`)
    }
    throw error
  }
}

export async function getOnlineKPIs(baseWeek: string, numWeeks: number = 8): Promise<OnlineKPIsResponse> {
  const response = await fetch(`${API_BASE_URL}/api/online-kpis?base_week=${baseWeek}&num_weeks=${numWeeks}`)
  if (!response.ok) {
    throw new Error(`Failed to fetch Online KPIs: ${response.statusText}`)
  }
  return response.json()
}

export async function getContribution(baseWeek: string, numWeeks: number = 8): Promise<ContributionResponse> {
  const response = await fetch(`${API_BASE_URL}/api/contribution?base_week=${baseWeek}&num_weeks=${numWeeks}`)
  if (!response.ok) {
    throw new Error(`Failed to fetch Contribution data: ${response.statusText}`)
  }
  return response.json()
}

export async function getGenderSales(baseWeek: string, numWeeks: number = 8): Promise<GenderSalesResponse> {
  const response = await fetch(`${API_BASE_URL}/api/gender-sales?base_week=${baseWeek}&num_weeks=${numWeeks}`)
  if (!response.ok) {
    throw new Error(`Failed to fetch Gender Sales data: ${response.statusText}`)
  }
  return response.json()
}

export async function getMenCategorySales(baseWeek: string, numWeeks: number = 8): Promise<MenCategorySalesResponse> {
  const response = await fetch(`${API_BASE_URL}/api/men-category-sales?base_week=${baseWeek}&num_weeks=${numWeeks}`)
  if (!response.ok) {
    throw new Error(`Failed to fetch Men Category Sales data: ${response.statusText}`)
  }
  return response.json()
}

export async function getWomenCategorySales(baseWeek: string, numWeeks: number = 8): Promise<WomenCategorySalesResponse> {
  const response = await fetch(`${API_BASE_URL}/api/women-category-sales?base_week=${baseWeek}&num_weeks=${numWeeks}`)
  if (!response.ok) {
    throw new Error(`Failed to fetch Women Category Sales data: ${response.statusText}`)
  }
  return response.json()
}

export async function getCategorySales(baseWeek: string, numWeeks: number = 8): Promise<CategorySalesResponse> {
  const response = await fetch(`${API_BASE_URL}/api/category-sales?base_week=${baseWeek}&num_weeks=${numWeeks}`)
  if (!response.ok) {
    throw new Error(`Failed to fetch Category Sales data: ${response.statusText}`)
  }
  return response.json()
}

export interface ProductData {
  rank: number
  gender: string
  category: string
  product: string
  color: string
  gross_revenue: number
  sales_qty: number
}

export interface TopProductsData {
  week: string
  products: ProductData[]
  top_total: {
    gross_revenue: number
    sales_qty: number
    sob: number
  }
  grand_total: {
    gross_revenue: number
    sales_qty: number
    sob: number
  }
}

export interface TopProductsResponse {
  top_products: TopProductsData[]
  period_info: {
    latest_week: string
    latest_dates: string
  }
}

export interface SessionsPerCountryData {
  week: string
  countries: Record<string, number>
  last_year?: {
    week: string
    countries: Record<string, number>
  } | null
}

export interface SessionsPerCountryResponse {
  sessions_per_country: SessionsPerCountryData[]
  period_info: {
    latest_week: string
    latest_dates: string
  }
}

export interface ConversionPerCountryData {
  week: string
  countries: Record<string, {
    conversion_rate: number
    orders: number
    sessions: number
  }>
  last_year?: {
    week: string
    countries: Record<string, {
      conversion_rate: number
      orders: number
      sessions: number
    }>
  } | null
}

export interface ConversionPerCountryResponse {
  conversion_per_country: ConversionPerCountryData[]
  period_info: {
    latest_week: string
    latest_dates: string
  }
}

export interface NewCustomersPerCountryData {
  week: string
  countries: Record<string, number>
  last_year?: {
    week: string
    countries: Record<string, number>
  } | null
}

export interface NewCustomersPerCountryResponse {
  new_customers_per_country: NewCustomersPerCountryData[]
  period_info: {
    latest_week: string
    latest_dates: string
  }
}

export interface ReturningCustomersPerCountryData {
  week: string
  countries: Record<string, number>
  last_year?: {
    week: string
    countries: Record<string, number>
  } | null
}

export interface ReturningCustomersPerCountryResponse {
  returning_customers_per_country: ReturningCustomersPerCountryData[]
  period_info: {
    latest_week: string
    latest_dates: string
  }
}

export interface AOVNewCustomersPerCountryData {
  week: string
  countries: Record<string, number>
  last_year?: {
    week: string
    countries: Record<string, number>
  } | null
}

export interface AOVNewCustomersPerCountryResponse {
  aov_new_customers_per_country: AOVNewCustomersPerCountryData[]
  period_info: {
    latest_week: string
    latest_dates: string
  }
}

export interface AOVReturningCustomersPerCountryData {
  week: string
  countries: Record<string, number>
  last_year?: {
    week: string
    countries: Record<string, number>
  } | null
}

export interface AOVReturningCustomersPerCountryResponse {
  aov_returning_customers_per_country: AOVReturningCustomersPerCountryData[]
  period_info: {
    latest_week: string
    latest_dates: string
  }
}

export interface MarketingSpendPerCountryData {
  week: string
  countries: Record<string, number>
  last_year?: {
    week: string
    countries: Record<string, number>
  } | null
}

export interface MarketingSpendPerCountryResponse {
  marketing_spend_per_country: MarketingSpendPerCountryData[]
  period_info: {
    latest_week: string
    latest_dates: string
  }
}

export interface nCACPerCountryData {
  week: string
  countries: Record<string, number>
  last_year?: {
    week: string
    countries: Record<string, number>
  } | null
}

export interface nCACPerCountryResponse {
  ncac_per_country: nCACPerCountryData[]
  period_info: {
    latest_week: string
    latest_dates: string
  }
}

export interface ContributionNewPerCountryData {
  week: string
  countries: Record<string, number>
  last_year?: {
    week: string
    countries: Record<string, number>
  } | null
}

export interface ContributionNewPerCountryResponse {
  contribution_new_per_country: ContributionNewPerCountryData[]
  period_info: {
    latest_week: string
    latest_dates: string
  }
}

export interface ContributionNewTotalPerCountryResponse {
  contribution_new_total_per_country: ContributionNewPerCountryData[]
  period_info: {
    latest_week: string
    latest_dates: string
  }
}

export interface ContributionReturningPerCountryResponse {
  contribution_returning_per_country: ContributionNewPerCountryData[]
  period_info: {
    latest_week: string
    latest_dates: string
  }
}

export interface ContributionReturningTotalPerCountryResponse {
  contribution_returning_total_per_country: ContributionNewPerCountryData[]
  period_info: {
    latest_week: string
    latest_dates: string
  }
}

export interface TotalContributionPerCountryResponse {
  total_contribution_per_country: ContributionNewPerCountryData[]
  period_info: {
    latest_week: string
    latest_dates: string
  }
}

export async function getTopProducts(baseWeek: string, numWeeks: number = 1, topN: number = 20, customerType: 'new' | 'returning' = 'new'): Promise<TopProductsResponse> {
  const response = await fetch(`${API_BASE_URL}/api/top-products?base_week=${baseWeek}&num_weeks=${numWeeks}&top_n=${topN}&customer_type=${customerType}`)
  if (!response.ok) {
    throw new Error(`Failed to fetch Top Products data: ${response.statusText}`)
  }
  return response.json()
}

export async function getTopProductsByGender(baseWeek: string, numWeeks: number = 1, topN: number = 20, genderFilter: 'men' | 'women' = 'men'): Promise<TopProductsResponse> {
  const response = await fetch(`${API_BASE_URL}/api/top-products-gender?base_week=${baseWeek}&num_weeks=${numWeeks}&top_n=${topN}&gender_filter=${genderFilter}`)
  if (!response.ok) {
    throw new Error(`Failed to fetch Top Products by Gender data: ${response.statusText}`)
  }
  return response.json()
}

export async function getSessionsPerCountry(baseWeek: string, numWeeks: number = 8): Promise<SessionsPerCountryResponse> {
  const response = await fetch(`${API_BASE_URL}/api/sessions-per-country?base_week=${baseWeek}&num_weeks=${numWeeks}`)
  if (!response.ok) {
    throw new Error(`Failed to fetch Sessions per Country data: ${response.statusText}`)
  }
  return response.json()
}

export async function getConversionPerCountry(baseWeek: string, numWeeks: number = 8): Promise<ConversionPerCountryResponse> {
  const response = await fetch(`${API_BASE_URL}/api/conversion-per-country?base_week=${baseWeek}&num_weeks=${numWeeks}`)
  if (!response.ok) {
    throw new Error(`Failed to fetch Conversion per Country data: ${response.statusText}`)
  }
  return response.json()
}

export async function getNewCustomersPerCountry(baseWeek: string, numWeeks: number = 8): Promise<NewCustomersPerCountryResponse> {
  const response = await fetch(`${API_BASE_URL}/api/new-customers-per-country?base_week=${baseWeek}&num_weeks=${numWeeks}`)
  if (!response.ok) {
    throw new Error(`Failed to fetch New Customers per Country data: ${response.statusText}`)
  }
  return response.json()
}

export async function getReturningCustomersPerCountry(baseWeek: string, numWeeks: number = 8): Promise<ReturningCustomersPerCountryResponse> {
  const response = await fetch(`${API_BASE_URL}/api/returning-customers-per-country?base_week=${baseWeek}&num_weeks=${numWeeks}`)
  if (!response.ok) {
    throw new Error(`Failed to fetch Returning Customers per Country data: ${response.statusText}`)
  }
  return response.json()
}

export async function getAOVNewCustomersPerCountry(baseWeek: string, numWeeks: number = 8): Promise<AOVNewCustomersPerCountryResponse> {
  const response = await fetch(`${API_BASE_URL}/api/aov-new-customers-per-country?base_week=${baseWeek}&num_weeks=${numWeeks}`)
  if (!response.ok) {
    throw new Error(`Failed to fetch AOV New Customers per Country data: ${response.statusText}`)
  }
  return response.json()
}

export async function getAOVReturningCustomersPerCountry(baseWeek: string, numWeeks: number = 8): Promise<AOVReturningCustomersPerCountryResponse> {
  const response = await fetch(`${API_BASE_URL}/api/aov-returning-customers-per-country?base_week=${baseWeek}&num_weeks=${numWeeks}`)
  if (!response.ok) {
    throw new Error(`Failed to fetch AOV Returning Customers per Country data: ${response.statusText}`)
  }
  return response.json()
}

export async function getMarketingSpendPerCountry(baseWeek: string, numWeeks: number = 8): Promise<MarketingSpendPerCountryResponse> {
  const response = await fetch(`${API_BASE_URL}/api/marketing-spend-per-country?base_week=${baseWeek}&num_weeks=${numWeeks}`)
  if (!response.ok) {
    throw new Error(`Failed to fetch Marketing Spend per Country data: ${response.statusText}`)
  }
  return response.json()
}

export async function getNCACPerCountry(baseWeek: string, numWeeks: number = 8): Promise<nCACPerCountryResponse> {
  const response = await fetch(`${API_BASE_URL}/api/ncac-per-country?base_week=${baseWeek}&num_weeks=${numWeeks}`)
  if (!response.ok) {
    throw new Error(`Failed to fetch nCAC per Country data: ${response.statusText}`)
  }
  return response.json()
}

export async function getContributionNewPerCountry(baseWeek: string, numWeeks: number = 8): Promise<ContributionNewPerCountryResponse> {
  const response = await fetch(`${API_BASE_URL}/api/contribution-new-per-country?base_week=${baseWeek}&num_weeks=${numWeeks}`)
  if (!response.ok) {
    throw new Error(`Failed to fetch Contribution New per Country data: ${response.statusText}`)
  }
  return response.json()
}

export async function getContributionNewTotalPerCountry(baseWeek: string, numWeeks: number = 8): Promise<ContributionNewTotalPerCountryResponse> {
  const response = await fetch(`${API_BASE_URL}/api/contribution-new-total-per-country?base_week=${baseWeek}&num_weeks=${numWeeks}`)
  if (!response.ok) {
    throw new Error(`Failed to fetch Contribution New Total per Country data: ${response.statusText}`)
  }
  return response.json()
}

export async function getContributionReturningPerCountry(baseWeek: string, numWeeks: number = 8): Promise<ContributionReturningPerCountryResponse> {
  const response = await fetch(`${API_BASE_URL}/api/contribution-returning-per-country?base_week=${baseWeek}&num_weeks=${numWeeks}`)
  if (!response.ok) {
    throw new Error(`Failed to fetch Contribution Returning per Country data: ${response.statusText}`)
  }
  return response.json()
}

export async function getContributionReturningTotalPerCountry(baseWeek: string, numWeeks: number = 8): Promise<ContributionReturningTotalPerCountryResponse> {
  const response = await fetch(`${API_BASE_URL}/api/contribution-returning-total-per-country?base_week=${baseWeek}&num_weeks=${numWeeks}`)
  if (!response.ok) {
    throw new Error(`Failed to fetch Contribution Returning Total per Country data: ${response.statusText}`)
  }
  return response.json()
}

export async function getTotalContributionPerCountry(baseWeek: string, numWeeks: number = 8): Promise<TotalContributionPerCountryResponse> {
  const response = await fetch(`${API_BASE_URL}/api/total-contribution-per-country?base_week=${baseWeek}&num_weeks=${numWeeks}`)
  if (!response.ok) {
    throw new Error(`Failed to fetch Total Contribution per Country data: ${response.statusText}`)
  }
  return response.json()
}

export interface BatchMetricsResponse {
  periods: PeriodsResponse
  metrics: MetricsResponse
  markets: MarketsResponse
  kpis: OnlineKPIsResponse
  contribution: ContributionResponse
  gender_sales: GenderSalesResponse
  men_category_sales: MenCategorySalesResponse
  women_category_sales: WomenCategorySalesResponse
  category_sales: any
  products_new: any
  products_gender: any
  sessions_per_country: SessionsPerCountryResponse
  conversion_per_country: ConversionPerCountryResponse
  new_customers_per_country: NewCustomersPerCountryResponse
  returning_customers_per_country: ReturningCustomersPerCountryResponse
  aov_new_customers_per_country: AOVNewCustomersPerCountryResponse
  aov_returning_customers_per_country: AOVReturningCustomersPerCountryResponse
  marketing_spend_per_country: MarketingSpendPerCountryResponse
  ncac_per_country: nCACPerCountryResponse
  contribution_new_per_country: ContributionNewPerCountryResponse
  contribution_new_total_per_country: ContributionNewTotalPerCountryResponse
  contribution_returning_per_country: ContributionReturningPerCountryResponse
  contribution_returning_total_per_country: ContributionReturningTotalPerCountryResponse
  total_contribution_per_country: TotalContributionPerCountryResponse
}

export async function getBatchMetrics(baseWeek: string, numWeeks: number = 8): Promise<BatchMetricsResponse> {
  const response = await fetch(`${API_BASE_URL}/api/batch/all-metrics?base_week=${baseWeek}&num_weeks=${numWeeks}`)
  if (!response.ok) {
    throw new Error(`Failed to fetch batch metrics: ${response.statusText}`)
  }
  return response.json()
}

export async function generatePDF(baseWeek: string, periods: string[]): Promise<GeneratePDFResponse> {
  const response = await fetch(`${API_BASE_URL}/api/generate/pdf`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      base_week: baseWeek,
      periods: periods,
    }),
  })
  
  if (!response.ok) {
    throw new Error(`Failed to generate PDF: ${response.statusText}`)
  }
  return response.json()
}

export function getDownloadUrl(filename: string): string {
  return `${API_BASE_URL}/api/download/${filename}`
}

// PDFGenerationProgress is now PDFProgressUpdate (see above)

export interface PDFProgressUpdate {
  step: string
  stepNumber: number
  totalSteps: number
  message: string
  currentPage?: string | null
  percentage: number
  result?: GeneratePDFResponse
  error?: string
}

export async function generateWeeklyReportsPDF(
  baseWeek: string,
  periods: string[],
  onProgress?: (progress: PDFProgressUpdate) => void
): Promise<GeneratePDFResponse> {
  try {
    // Use Server-Sent Events (SSE) for real-time progress updates
    // Backend will send progress updates for each page as it's being screenshotted
    try {
      const response = await fetch(`${API_BASE_URL}/api/generate/weekly-reports-pdf`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ base_week: baseWeek, periods }),
      })
      
      if (!response.ok) {
        throw new Error(`Failed to start PDF generation: ${response.statusText}`)
      }
      
      if (!response.body) {
        throw new Error('No response body from server')
      }
      
      const reader = response.body.getReader()
      const decoder = new TextDecoder()
      let buffer = ''
      let result: GeneratePDFResponse | null = null
      
      while (true) {
        const { done, value } = await reader.read()
        
        if (done) {
          break
        }
        
        buffer += decoder.decode(value, { stream: true })
        
        // Process complete SSE events
        const lines = buffer.split('\n')
        buffer = lines.pop() || '' // Keep incomplete line in buffer
        
        for (const line of lines) {
          if (line.trim() === '') continue // Skip empty lines
          if (line.startsWith('data: ')) {
            try {
              const jsonStr = line.slice(6).trim()
              if (!jsonStr) continue // Skip empty data lines
              
              const data = JSON.parse(jsonStr)
              
              // Debug logging (only for non-heartbeat updates)
              if (data.step !== 'processing' && data.step !== 'heartbeat') {
                console.log('📊 PDF Progress Update:', {
                  step: data.step,
                  stepNumber: data.stepNumber,
                  totalSteps: data.totalSteps,
                  message: data.message,
                  currentPage: data.currentPage,
                  percentage: data.percentage,
                  hasError: !!data.error,
                  hasResult: !!data.result
                })
              }
              
              // Report progress update
              if (onProgress) {
                onProgress({
                  step: data.step || 'unknown',
                  stepNumber: data.stepNumber || 0,
                  totalSteps: data.totalSteps || 1,
                  message: data.message || 'Processing...',
                  currentPage: data.currentPage,
                  percentage: data.percentage || 0,
                  result: data.result,
                  error: data.error
                })
              }
              
              // If we got an error, throw it immediately (this will break the loop)
              if (data.error) {
                console.error('❌ PDF Generation Error:', data.error)
                throw new Error(data.error)
              }
              
              // If step is 'error' but no error message, throw generic error
              if (data.step === 'error' && !data.error) {
                console.error('❌ PDF Generation Error (unknown):', data)
                throw new Error('PDF generation failed with unknown error')
              }
              
              // If we got a result, store it
              if (data.result) {
                result = data.result
                console.log('✅ PDF Generation Result:', result)
              }
              
            } catch (parseError) {
              console.warn('Failed to parse SSE data:', parseError, 'Line:', line)
            }
          } else if (line.trim() !== '') {
            // Log non-SSE lines for debugging
            console.debug('Non-SSE line received:', line)
          }
        }
      }
      
      // Check if we got an error during the process
      if (!result) {
        // Check if we received any error messages in progress updates
        // If we reached here without result, it means the stream ended but no result was sent
        // This could mean:
        // 1. An error occurred but wasn't caught properly
        // 2. The backend didn't send the final result
        // 3. The stream ended prematurely
        throw new Error('PDF generation completed but no result was returned. The backend may have encountered an error. Check backend logs for details.')
      }
      
      return result
      
    } catch (fetchError: any) {
      if (fetchError.name === 'AbortError' || fetchError.name === 'TimeoutError') {
        throw new Error('PDF generation timed out. Please try again.')
      } else if (fetchError.message?.includes('Failed to fetch') || fetchError.message?.includes('network')) {
        throw new Error('Unable to connect to backend server. Please ensure the backend is running on port 8000.')
      } else {
        throw new Error(`Network error: ${fetchError.message || 'Failed to connect to server'}`)
      }
    }
  } catch (error: any) {
    if (onProgress) {
      onProgress({
        step: 'error',
        stepNumber: 0,
        totalSteps: 1,
        message: `Error: ${error.message || 'Failed to generate PDF'}`,
        currentPage: null,
        percentage: 0,
        error: error.message
      })
    }
    throw error
  }
}

// Budget APIs
export interface BudgetGeneralResponse {
  week: string
  months: string[]
  metrics: string[]
  table: Record<string, Record<string, number>>
  totals?: Record<string, number>
  ytd_totals?: Record<string, number>
  customer_by_metric?: Record<string, string>
  display_name_by_metric?: Record<string, string>
}

export interface ActualsGeneralResponse {
  week: string
  months: string[]
  metrics: string[]
  table: Record<string, Record<string, number>>
  totals?: Record<string, number>
  ytd_totals?: Record<string, number>
}

export async function getBudgetGeneral(baseWeek: string): Promise<BudgetGeneralResponse> {
  const response = await fetch(`${API_BASE_URL}/api/budget-general?week=${baseWeek}`)
  if (!response.ok) {
    throw new Error(`Failed to fetch budget general: ${response.statusText}`)
  }
  return response.json()
}

export async function getActualsGeneral(baseWeek: string): Promise<ActualsGeneralResponse> {
  const response = await fetch(`${API_BASE_URL}/api/actuals-general?week=${baseWeek}`)
  if (!response.ok) {
    throw new Error(`Failed to fetch actuals general: ${response.statusText}`)
  }
  return response.json()
}

// Budget raw data (markets page prototype)
export interface BudgetRawResponse {
  columns: string[]
  sample_data: Array<Record<string, any>>
}

export async function getBudgetRaw(baseWeek: string): Promise<BudgetRawResponse> {
  const response = await fetch(`${API_BASE_URL}/api/budget-data?week=${baseWeek}`)
  if (!response.ok) {
    throw new Error(`Failed to fetch budget raw: ${response.statusText}`)
  }
  return response.json()
}

export async function getActualsMarkets(baseWeek: string): Promise<BudgetRawResponse> {
  const response = await fetch(`${API_BASE_URL}/api/actuals-markets?week=${baseWeek}`)
  if (!response.ok) {
    throw new Error(`Failed to fetch actuals markets: ${response.statusText}`)
  }
  return response.json()
}

export interface ActualsMarketsDetailedResponse {
  week: string
  months: string[]
  markets: string[]
  metrics: string[]
  table: Record<string, Record<string, Record<string, number>>> // market -> metric -> month -> value
  totals: Record<string, Record<string, number>> // market -> metric -> total
  ytd_totals: Record<string, Record<string, number>> // market -> metric -> ytd
}

export async function getActualsMarketsDetailed(baseWeek: string): Promise<ActualsMarketsDetailedResponse> {
  const response = await fetch(`${API_BASE_URL}/api/actuals-markets-detailed?week=${baseWeek}`)
  if (!response.ok) {
    throw new Error(`Failed to fetch actuals markets detailed: ${response.statusText}`)
  }
  return response.json()
}

export interface SupabaseSyncResponse {
  success: boolean
  week: string
  row_counts: Record<string, number>
  elapsed_seconds: number
  sync_id?: string
  error?: string
}

export async function syncSupabase(baseWeek: string): Promise<SupabaseSyncResponse> {
  try {
    const response = await fetch(`${API_BASE_URL}/api/sync-supabase?week=${baseWeek}`, {
      method: 'POST',
      signal: AbortSignal.timeout(180000) // 180 second timeout (3 minutes) - sync can take 97+ seconds
    })
    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: response.statusText }))
      throw new Error(error.detail || `Failed to sync Supabase: ${response.statusText}`)
    }
    return response.json()
  } catch (error: any) {
    if (error.name === 'TimeoutError' || error.name === 'AbortError') {
      throw new Error(`Request timeout: Supabase sync took too long (over 3 minutes). The sync may still be processing in the background.`)
    }
    if (error.message?.includes('Failed to fetch') || error.message?.includes('NetworkError') || error.message?.includes('ERR_NETWORK_IO_SUSPENDED')) {
      throw new Error(`Network error: Unable to connect to backend server at ${API_BASE_URL}. The sync may still be processing in the background.`)
    }
    throw error
  }
}
