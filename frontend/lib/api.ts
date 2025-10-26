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
