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
  const response = await fetch(`${API_BASE_URL}/api/markets/top?base_week=${baseWeek}&num_weeks=${numWeeks}`)
  if (!response.ok) {
    throw new Error(`Failed to fetch markets: ${response.statusText}`)
  }
  return response.json()
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
