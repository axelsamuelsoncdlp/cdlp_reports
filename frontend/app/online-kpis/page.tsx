'use client'

import { useState, useEffect } from 'react'
import { getPeriods, getOnlineKPIs, type OnlineKPIsResponse } from '@/lib/api'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { ChartConfig, ChartContainer, ChartTooltip, ChartTooltipContent } from '@/components/ui/chart'
import { CartesianGrid, LabelList, Line, LineChart, XAxis } from 'recharts'
import { Skeleton } from '@/components/ui/skeleton'
import { Loader2 } from 'lucide-react'

export default function OnlineKPIs() {
  const [selectedWeek, setSelectedWeek] = useState('2025-42')
  const [periods, setPeriods] = useState(null)
  const [kpisData, setKpisData] = useState<OnlineKPIsResponse | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  // Load periods on mount
  useEffect(() => {
    const loadPeriods = async () => {
      try {
        const data = await getPeriods(selectedWeek)
        setPeriods(data)
      } catch (err) {
        console.error('Failed to load periods:', err)
      }
    }
    loadPeriods()
  }, [selectedWeek])

  // Load KPIs data
  useEffect(() => {
    if (!periods) return

    const loadKPIs = async () => {
      // Check cache first BEFORE setting loading state
      const cacheKey = `online_kpis_${selectedWeek}`
      try {
        const cachedData = localStorage.getItem(cacheKey)
        if (cachedData) {
          const parsed = JSON.parse(cachedData)
          const cacheAge = Date.now() - parsed.timestamp
          if (cacheAge < 60 * 60 * 1000) { // 1 hour
            setKpisData(parsed.data)
            return // Don't show loading if cached
          }
        }
      } catch (err) {
        console.warn('Failed to load from cache:', err)
      }
      
      // Only show loading if we need to fetch from API
      setLoading(true)
      setError(null)
      
      try {
        const data = await getOnlineKPIs(selectedWeek, 8)
        setKpisData(data)
        
        // Cache the data
        try {
          localStorage.setItem(cacheKey, JSON.stringify({
            data: data,
            timestamp: Date.now()
          }))
        } catch (err) {
          console.warn('Failed to save to cache:', err)
        }
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to fetch Online KPIs')
      } finally {
        setLoading(false)
      }
    }

    loadKPIs()
  }, [periods, selectedWeek])

  const kpiLabels = [
    { key: 'sessions', label: 'Sessions', format: (val: number) => Math.round(val / 1000).toString() + 'k' },
    { key: 'aov_new_customer', label: 'AOV New Customer', format: (val: number) => Math.round(val).toString() },
    { key: 'aov_returning_customer', label: 'AOV Returning Customer', format: (val: number) => Math.round(val).toString() },
    { key: 'cos', label: 'Marketing Spend', format: (val: number) => Math.round(val / 1000).toString() + 'k' },
    { key: 'conversion_rate', label: 'Conversion Rate', format: (val: number) => Math.round(val * 100).toString() + '%' },
    { key: 'new_customers', label: 'New Customers', format: (val: number) => val.toLocaleString() },
    { key: 'returning_customers', label: 'Returning Customers', format: (val: number) => val.toLocaleString() },
    { key: 'new_customer_cac', label: 'New Customer CAC', format: (val: number) => Math.round(val).toString() },
    { key: 'total_orders', label: 'Total Orders', format: (val: number) => val.toLocaleString() }
  ]

  if (loading) {
    return (
      <div className="space-y-8">
        <div className="flex items-center gap-3 mb-6">
          <Loader2 className="h-6 w-6 animate-spin text-primary" />
          <div>
            <h2 className="text-lg font-semibold text-gray-900">Loading Online KPIs</h2>
            <p className="text-sm text-gray-600">Processing data from Qlik, DEMA, and Shopify...</p>
          </div>
        </div>
        
        <div className="grid grid-cols-3 gap-6">
          {kpiLabels.map((kpi, index) => (
            <Card key={index}>
              <CardHeader>
                <Skeleton className="h-5 w-48" />
              </CardHeader>
              <CardContent>
                <Skeleton className="h-48 w-full" />
              </CardContent>
            </Card>
          ))}
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="space-y-8">
        <div className="bg-white rounded-lg shadow p-6">
          <div className="text-red-600">{error}</div>
        </div>
      </div>
    )
  }

  if (!kpisData) {
    return (
      <div className="space-y-8">
        <div className="bg-white rounded-lg shadow p-6 text-center">
          <p className="text-gray-600">No KPIs data available</p>
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-8">
      <div className="grid grid-cols-3 gap-6">
        {kpiLabels.map((kpi, index) => {
          // Reverse data to show latest week (42) on the right
          const chartData = kpisData.kpis.map(k => {
            const weekNum = k.week.split('-')[1]
            const currentValue = k[kpi.key as keyof typeof k] as number
            const lastYearValue = k.last_year?.[kpi.key as keyof typeof k.last_year] as number || 0
            
            return {
              week: `W${weekNum}`,
              current: currentValue,
              lastYear: lastYearValue
            }
          }).reverse()

          const chartConfig = {
            current: {
              label: "Current Year",
              color: "var(--chart-1)",
            },
            lastYear: {
              label: "Last Year",
              color: "var(--chart-2)",
            },
          } satisfies ChartConfig

          return (
            <Card key={index}>
              <CardHeader>
                <CardTitle>{kpi.label}</CardTitle>
              </CardHeader>
              <CardContent>
                <ChartContainer config={chartConfig}>
                  <LineChart
                    accessibilityLayer
                    data={chartData}
                    margin={{
                      top: 20,
                      left: 12,
                      right: 12,
                    }}
                  >
                    <CartesianGrid vertical={false} />
                    <XAxis
                      dataKey="week"
                      tickLine={false}
                      axisLine={false}
                      tickMargin={8}
                      tickFormatter={(value) => value.slice(0, 3)}
                    />
                    <ChartTooltip
                      cursor={false}
                      content={<ChartTooltipContent indicator="line" />}
                    />
                    <Line
                      dataKey="current"
                      type="natural"
                      stroke="var(--color-current)"
                      strokeWidth={2}
                      dot={{
                        fill: "var(--color-current)",
                      }}
                      activeDot={{
                        r: 6,
                      }}
                    >
                      <LabelList
                        position="top"
                        offset={12}
                        className="fill-foreground"
                        fontSize={12}
                        formatter={(value: number) => kpi.format(value)}
                      />
                    </Line>
                    <Line
                      dataKey="lastYear"
                      type="natural"
                      stroke="var(--color-lastYear)"
                      strokeWidth={2}
                      dot={{
                        fill: "var(--color-lastYear)",
                      }}
                      activeDot={{
                        r: 6,
                      }}
                    />
                  </LineChart>
                </ChartContainer>
              </CardContent>
            </Card>
          )
        })}
      </div>
    </div>
  )
}
