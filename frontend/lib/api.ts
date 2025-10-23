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
