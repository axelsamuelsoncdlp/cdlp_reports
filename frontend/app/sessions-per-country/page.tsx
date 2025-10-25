'use client'

import { useSessionsPerCountry } from '@/contexts/DataCacheContext'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { ChartConfig, ChartContainer, ChartTooltip, ChartTooltipContent } from '@/components/ui/chart'
import { CartesianGrid, LabelList, Line, LineChart, XAxis } from 'recharts'
import { Skeleton } from '@/components/ui/skeleton'
import { Loader2 } from 'lucide-react'

export default function SessionsPerCountry() {
  const { sessions_per_country } = useSessionsPerCountry()

  // Define country order and labels
  const countryOrder = [
    { key: 'Total', label: 'Total' },
    { key: 'USA', label: 'USA' },
    { key: 'UK', label: 'UK' },
    { key: 'Sweden', label: 'Sverige' },
    { key: 'Germany', label: 'Tyskland' },
    { key: 'Australia', label: 'Australien' },
    { key: 'Canada', label: 'Kanada' },
    { key: 'France', label: 'Frankrike' },
    { key: 'ROW', label: 'ROW' }
  ]

  const formatValue = (value: number): string => {
    if (value === 0) return '0'
    return Math.round(value).toLocaleString('sv-SE')
  }

  if (!sessions_per_country) {
    return (
      <div className="space-y-8">
        <div className="flex items-center gap-3 mb-6">
          <Loader2 className="h-6 w-6 animate-spin text-primary" />
          <div>
            <h2 className="text-lg font-semibold text-gray-900">Loading Sessions per Country</h2>
            <p className="text-sm text-gray-600">Processing sessions data by country...</p>
          </div>
        </div>
        
        <div className="grid grid-cols-3 gap-6">
          {countryOrder.map((_, index) => (
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

  return (
    <div className="space-y-8">
      <div className="grid grid-cols-3 gap-6">
        {countryOrder.map((country, index) => {
          const chartData = sessions_per_country.sessions_per_country.map((week: any) => {
            const weekNum = week.week.split('-')[1]
            let currentValue = 0
            let lastYearValue = 0

            if (country.key === 'Total') {
              // Calculate total sessions across all countries
              currentValue = Object.values(week.countries).reduce((sum: number, val: any) => sum + val, 0)
              if (week.last_year) {
                lastYearValue = Object.values(week.last_year.countries).reduce((sum: number, val: any) => sum + val, 0)
              }
            } else if (country.key === 'ROW') {
              // Calculate ROW (Rest of World) - all countries except the main ones
              const mainCountries = ['USA', 'UK', 'Sweden', 'Germany', 'Australia', 'Canada', 'France']
              currentValue = Object.entries(week.countries).reduce((sum: number, [countryName, sessions]: [string, any]) => {
                if (!mainCountries.includes(countryName)) {
                  return sum + sessions
                }
                return sum
              }, 0)
              if (week.last_year) {
                lastYearValue = Object.entries(week.last_year.countries).reduce((sum: number, [countryName, sessions]: [string, any]) => {
                  if (!mainCountries.includes(countryName)) {
                    return sum + sessions
                  }
                  return sum
                }, 0)
              }
            } else {
              // Specific country
              currentValue = week.countries[country.key] || 0
              if (week.last_year) {
                lastYearValue = week.last_year.countries[country.key] || 0
              }
            }
            
            return {
              week: `W${weekNum}`,
              current: currentValue,
              lastYear: lastYearValue
            }
          })

          const chartConfig = {
            current: {
              label: "Current Year",
              color: "#4B5563",
            },
            lastYear: {
              label: "Last Year",
              color: "#F97316",
            },
          } satisfies ChartConfig

          return (
            <Card key={country.key}>
              <CardHeader>
                <CardTitle>{country.label}</CardTitle>
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
                      tickFormatter={(value) => value.replace('W', '')}
                    />
                    <ChartTooltip
                      cursor={false}
                      content={<ChartTooltipContent indicator="line" />}
                    />
                    <Line
                      dataKey="current"
                      type="natural"
                      stroke="#4B5563"
                      strokeWidth={2}
                    >
                      <LabelList
                        position="top"
                        offset={12}
                        fill="#4B5563"
                        fontSize={12}
                        formatter={(value: number) => formatValue(value)}
                      />
                    </Line>
                    <Line
                      dataKey="lastYear"
                      type="natural"
                      stroke="#F97316"
                      strokeWidth={2}
                      strokeDasharray="5 5"
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
