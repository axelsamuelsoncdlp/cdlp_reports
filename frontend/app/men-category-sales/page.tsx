'use client'

import { useMenCategorySales } from '@/contexts/DataCacheContext'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { ChartConfig, ChartContainer, ChartTooltip, ChartTooltipContent } from '@/components/ui/chart'
import { CartesianGrid, LabelList, Line, LineChart, XAxis } from 'recharts'
import { Skeleton } from '@/components/ui/skeleton'
import { Loader2 } from 'lucide-react'

export default function MenCategorySales() {
  const { men_category_sales } = useMenCategorySales()

  if (!men_category_sales) {
    return (
      <div className="space-y-8">
        <div className="flex items-center gap-3 mb-6">
          <Loader2 className="h-6 w-6 animate-spin text-primary" />
          <div>
            <h2 className="text-lg font-semibold text-gray-900">Loading Men Category Sales</h2>
            <p className="text-sm text-gray-600">Processing sales data by product category...</p>
          </div>
        </div>
        
        <div className="grid grid-cols-3 gap-6">
          {[1, 2, 3, 4, 5, 6, 7].map((index) => (
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

  // Get all unique categories across all weeks
  const allCategories = new Set<string>()
  men_category_sales.men_category_sales.forEach(week => {
    Object.keys(week.categories).forEach(cat => allCategories.add(cat))
  })

  // Calculate total sales for each category and sort by highest to lowest
  const categoryTotals = Array.from(allCategories).map(category => {
    const total = men_category_sales.men_category_sales.reduce((sum, week) => {
      return sum + (week.categories[category] || 0)
    }, 0)
    return { category, total }
  })

  // Sort by total sales descending
  const sortedCategories = categoryTotals.sort((a, b) => b.total - a.total).map(item => item.category)

  return (
    <div className="space-y-8">
      <div className="grid grid-cols-3 gap-6">
        {sortedCategories.map((category, index) => {
          const chartData = men_category_sales.men_category_sales.map(g => {
            const weekNum = g.week.split('-')[1]
            const currentValue = g.categories[category] || 0
            const lastYearValue = g.last_year?.categories[category] || 0
            
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
            <Card key={category}>
              <CardHeader>
                <CardTitle>{category}</CardTitle>
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
                        formatter={(value: number) => Math.round(value / 1000).toString()}
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

